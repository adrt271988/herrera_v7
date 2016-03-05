# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools

class mail_authorization(osv.osv):
    
    _name = "mail.authorization"
    _description = "Autorizaciones"
    
    def create(self, cr, uid, vals, context=None):
        vals.update({'reference':self.pool.get('ir.sequence').get(cr, uid, 'mail.authorization')})
        return super(mail_authorization, self).create(cr, uid, vals, context=context)
        
    _columns = {
        'name': fields.char('Descripción', size=200,required= True, help= 'Descripción de la Autorizacion'),
        'active': fields.boolean('Activo'),
        'user_ids': fields.many2many('res.users', 'authorizing_user', 'user_id', 'authorization_id','Autorizantes'),
        'reference': fields.char('Referencia', size=30, help= 'Codigo y/o nombre referencial de la autorizacion'),
        'date': fields.datetime('Fecha'),
        'contact': fields.char('Contacto', size=100,required= True, help= 'Departamento, persona u oficina a contactar para esta autorización'),
        'model': fields.char('Objeto', size=64, help="Nombre del modelo que contiene el método a ejecutar, ej. 'res.partner'."),
        'function': fields.char('Método', size=64, help="Nombre del el método a ser llamado cuando este 'done' una solicitud de este tipo de autorización, ej. write"),
        'args': fields.text('Argumentos', help="Argumentos a ser evaluado por el método, ej. {'state':done}."),
        'module': fields.char('Módulo', size=64, help="Nombre del modulo que contiene la vista, ej. 'base'."),
        'view_name': fields.char('Nombre de la vista', size=64, help="Vista perteneciente al módulo , ej. view_partner_form"),
        'view_type': fields.char('Tipo de vista', size=8, help="form, tree, kanban, etc."),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'active': True,
    }
mail_authorization()

class mail_authorization_request(osv.osv):
    
    _name = "mail.authorization.request"
    _inherit = "mail.thread"

    def _exec_action(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        autorz_obj = self.pool.get('mail.authorization')
        request = self.browse(cr, uid, ids, context=context)[0]
        autorzt = autorz_obj.browse(cr, uid, request.authorization_id.id, context=context)
        model = autorzt.model
        funct = autorzt.function
        args = autorzt.args
        res_id = request.res_id
        result = False
        expr = False
        if model and funct and res_id:
            expr = "self.pool.get('%s').%s(cr,uid,[%s])"%(model,funct,res_id)
            if args:
                expr = "self.pool.get('%s').%s(cr,uid,[%s],%s)"%(model,funct,res_id,args)
        if expr:
            result = eval(expr)
        return result
        
    def set_to_wait(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state':'wait'}, context)
        
    def set_to_done(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        result = False
        users = []
        autorz_obj = self.pool.get('mail.authorization')
        request = self.browse(cr, uid, ids, context=context)[0]
        autorzt = autorz_obj.browse(cr, uid, request.authorization_id.id, context=context)
        
        for user in autorzt.user_ids:
            users.append(user.id)
        if uid in users:
            result = self.write(cr, uid, ids, {'state':'done', 'authorizing_user': uid, 'date_end': time.strftime('%Y-%m-%d %H:%M:%S') }, context)
        else:
            raise osv.except_osv(_('Notificación!'), _('Ud no esta autorizado para aprobar esta solicitud. Verifique los contactos autorizantes que posee este tipo de autorización o contacte al administrador de servicios.'))
        if result:
            self._exec_action(cr, uid, ids, context=context)
        return result
        
    def set_to_close(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        users = []
        autorz_obj = self.pool.get('mail.authorization')
        request = self.browse(cr, uid, ids, context=context)[0]
        autorzt = autorz_obj.browse(cr, uid, request.authorization_id.id, context=context)
        
        for user in autorzt.user_ids:
            users.append(user.id)
        if uid in users:
            return self.write(cr, uid, ids, {'state':'close', 'authorizing_user': uid, 'date_end': time.strftime('%Y-%m-%d %H:%M:%S') }, context)
        else:
            raise osv.except_osv(_('Notificación!'), _('Ud no esta autorizado para rechazar esta solicitud. Solo los contactos autorizantes y/o rechazantes que posee este tipo de autorización pueden realizar este proceso.'))
    
    def view_model_data(self, cr, uid, ids, context=None):
        autorz_obj = self.pool.get('mail.authorization')
        request = self.browse(cr, uid, ids, context=context)[0]
        autorzt = autorz_obj.browse(cr, uid, request.authorization_id.id, context=context)
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, autorzt.module, autorzt.view_name)
        view_id = view_ref and view_ref[1] or False
        return {
            'view_type': autorzt.view_type,
            'view_mode': 'form',
            'res_id': request.res_id,
            'res_model': autorzt.model,
            'views': [(view_id, autorzt.view_type)],
            'type': 'ir.actions.act_window',
            'target': 'current',
            #~ 'context': context,
        }
    
    _columns = {
        'name': fields.char('Descripcion', size=200, required=True, readonly=True, states={'draft':[('readonly',False)]},  help= 'Módulo o situación donde se necesita de la autorización'),
        'user_id': fields.many2one('res.users', 'Solicitante', required=True, readonly=True, states={'draft':[('readonly',False)]}, ),
        'authorization_id': fields.many2one('mail.authorization', 'Autorizacion tipo', required=True, readonly=True, states={'draft':[('readonly',False)]}, ),
        'request_date': fields.datetime('Fecha de Solicitud', required=True, readonly=True, states={'draft':[('readonly',False)]}, ),
        'contact': fields.related('authorization_id', 'contact', type='char', size=64, relation='mail.authorization', string='Autorizante', help= 'Departamento, persona u oficina a contactar para esta autorización'),
        'ref': fields.char('Referencia origen', size=40, readonly=True, states={'draft':[('readonly',False)]},  help= 'Hace referencia al documento o proceso que originó la solicitud.'),
        'res_id': fields.integer('ID de referencia', readonly=True,),
        'model_id': fields.many2one('ir.model', 'Modelo', readonly=True, states={'draft':[('readonly',False)]}, ),
        'authorizing_user': fields.many2one('res.users', 'Autorizante', readonly=True ),
        'date_end': fields.datetime('Fecha de Autorización', readonly=True ),
        'note': fields.text('Detalles', readonly=True, states={'wait':[('readonly',False)]} ),
        'state': fields.selection([('draft','Borrador'),('wait','En Espera'),('done','Autorizada'),('close','Rechazada')], 'Status', required=True),
    }

    _defaults = {
        'state': 'draft',
    }
                
mail_authorization_request()
