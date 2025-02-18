# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from datetime import datetime

class inherited_partner(osv.osv):
    """
    Herrera Customizations for res.partner model
    """
    _inherit = "res.partner"

    def _default_property_account_payable(self, cr, uid, context=None):
        account_payable_id = self.pool.get('account.account').search(cr, uid, [('type','=','payable')], context=context)
        return account_payable_id and account_payable_id[0]

    def _default_property_account_receivable(self, cr, uid, context=None):
        account_receivable_id = self.pool.get('account.account').search(cr, uid, [('type','=','receivable')], context=context)
        return account_receivable_id and account_receivable_id[0]
    
    def set_supplier(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'supplier': True }
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def unset_supplier(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'supplier': False}
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def set_customer(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'customer': True }
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def unset_customer(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'customer': False}
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def set_credit_blocked(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'credit_blocked': True }
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def unset_credit_blocked(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals = {'credit_blocked': False}
        res = super(inherited_partner, self).write(cr, uid, ids, vals, context)
        return res
    
    def auth_credit_blocked(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        partner = self.browse(cr, uid, ids[0], context=context)
        request_obj = self.pool.get('mail.authorization.request')
        auth_id = False
        result = False
        name = partner.name
        credit_blocked = partner.credit_blocked
        if credit_blocked:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_unset_credit_blocked')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        else:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_set_credit_blocked')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        if auth_id:
            request_obj.create(cr, uid, {
                    'name': 'Solicitud para modificación de Cliente',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': partner.id,
            })        
        return result
        
    def auth_active(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        partner = self.browse(cr, uid, ids[0], context=context)
        request_obj = self.pool.get('mail.authorization.request')
        auth_id = False
        result = False
        name = partner.name
        active = partner.active
        if active:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_unset_active')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        else:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_set_active')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        if auth_id:
            request_obj.create(cr, uid, {
                    'name': 'Solicitud para modificación de Cliente',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': partner.id,
            })
        return result
    
    _columns = {
        'shop_id' : fields.many2one("sale.shop", "Sucursal"),
        'municipality_id' : fields.many2one("res.municipality", "Municipio"),
        'parish_id' : fields.many2one("res.parish", "Parroquia"),
        'city_id' : fields.many2one("res.city", "Ciudad"),
        'sector' : fields.many2one("res.sector", "Sector"),
        'zipcode_id' : fields.many2one("res.zipcode", "Cod. postal"),
        'freight_route_id' : fields.many2one("freight.route", "Ruta de flete"),
        'global_limit': fields.float('Limite de crédito global',  help = "Limite de credito normal multiplicado por la cantidad de vendedores asignados"),
        'special': fields.boolean('Contibuyente especial',  help = "Calificado por el SENIAT como agente de retención"),
        'sica_code': fields.char('Código SICA'),
        'pv_metros': fields.float('Metros', help = "Metros cuadrados del piso de venta"),
        'pv_islas': fields.integer('Islas', help = "Islas en piso de venta"),
        'pv_cabezales': fields.integer('Cabezales', help = "Cabezales en piso de venta"),
        'pv_cajas': fields.integer('Cajas registradoras', help = "Cantidad de cajas registradoras en piso de venta"),
        'pv_planchas': fields.integer('Planchas', help = "Planchas que tiene las islas del piso de venta"),
        'checkout': fields.integer('Checkout'),
        'credit_blocked': fields.boolean('Bloqueado', readonly=True, help = "Cliente de baja fiabilidad crediticia"),
    }
    
    _defaults = {
        'property_account_payable': _default_property_account_payable,
        'property_account_receivable': _default_property_account_receivable,
    }
    
inherited_partner()


