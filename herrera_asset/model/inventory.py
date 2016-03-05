# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools


class account_asset_inventory(osv.osv):
    
    _name = 'account.asset.inventory'
    _description = "Inventario de Activos"
    
    def set_to_open(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state':'open'}, context)

    def set_to_close(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state': 'close'}, context=context)

    def set_to_draft(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    _columns = {
                 'name': fields.char('Inventario', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}, help="Nombre para identificar el inventario a realizar."),
                 'code': fields.char('Codigo', size=25, readonly=True, states={'draft':[('readonly',False)]}, help="Codigo para referenciar el inventario a realizar."),
                 'user_id': fields.many2one('res.users', 'Usuario', readonly=True, help="Usuario que realiza y/o confirma el inventario"),
                 'employee_id': fields.many2one('hr.employee', 'Responsable', readonly=True, states={'draft':[('readonly',False)]}, help="Nombre del empleado al que se le realiza el inventario."),
                 'department_id': fields.many2one('hr.department','Departamento', readonly=True, states={'draft':[('readonly',False)]}, help="Nombre del Departamento donde se va a realizar el inventario."),
                 'shop_id' : fields.many2one('sale.shop', 'Sucursal', readonly=True, states={'draft':[('readonly',False)]}, help="Nombre de la sucursal donde se va a realizar el inventario."),
                 'date_inventory': fields.date('Fecha', required= True, readonly=True, states={'draft':[('readonly',False)]}, help="Fecha de inicio del inventario."),
                 'asset_ids' : fields.one2many('asset.inventory.line', 'wizard_id', 'Descripcion', readonly=False, states={'close':[('readonly',True)]}),
                 'type': fields.selection([('S','Inventario por Sucursal'),
                                           ('D','Inventario por Departamento'), 
                                           ('R','Inventario por Responsable')], 
                                           'Tipo de inventario', required=True, select=True, readonly=True, states={'draft':[('readonly',False)]}),
                 'state': fields.selection([('draft','Borrador'),('open','En ejecución'),('close','Finalizado'),('done','Ajustado')], 'Status', required=True,
                                  help="Cuando se crea un inventario, el estado por defecto es 'Borrador' y es solo en este estado donde se pueden modificar los datos generales.\n" \
                                       "Si se confirma el inventario, el estado será 'En ejecución' y solo podrán ser modificadas las lineas del inventario.\n" \
                                       "Usted puede finalizar manualmente un inventario. El estado ajustado se muestra una vez se haya ejecutado el proceso de ajuste de las incidencias encontradas en los activos."),
                }
    _defaults = {
                'state': 'draft',
                'user_id': lambda self, cr, uid, context: uid,
                 }
    
    def adjust_inventory(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        line_obj = self.pool.get('asset.inventory.line')
        line_ids = line_obj.search(cr, uid, [('wizard_id','=',ids[0])])
        line = line_obj.browse(cr, uid, line_ids)
        
        for val in line:
            asset_obj.write(cr, uid, val.asset_id.id, {  'shop_id': val.shop_id.id,
                                                         'employee_id': val.employee_id.id,
                                                         'department_id': val.department_id.id,
                                                         'serial': val.serial }, context=context)                                                     
        self.write(cr, uid, ids, {'state': 'done','user_id': uid}, context=context)
        return True
        
account_asset_inventory()
