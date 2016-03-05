# -*- encoding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime

class stock_create_global(osv.osv_memory):
    _name = "stock.create.global"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        #Esta función por defecto devuelve un diccionario, con los valores que se cargan por defecto
        res = super(stock_create_global, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if not 'active_ids' in context:
            return res
        if not 'active_model' in context:
            return res
        if context['active_model'] == 'stock.picking':
            ids = context['active_ids']
            for pick in self.pool.get('stock.picking').browse(cr, uid, ids):
                if pick.global_id.id:
                    #~ raise osv.except_osv(_('Error!'), _(u'El albarán %s del pedido %s ya fue confirmado en bajo el número de global %s'%(pick.name,pick.sale_id.name,pick.global_id.name)))
                    raise osv.except_osv(_('Operación inválida!'), _(u'El pedido %s ya fue confirmado en bajo el número de global %s'%(pick.sale_id.name,pick.global_id.name)))
        return res
        
    def create_global(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        pickout_obj = self.pool.get('stock.picking.out')
        picking_ids = context.get('active_ids', [])
        self.pool.get('stock.picking.out').create_global(cr, uid, picking_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'sure' :fields.boolean('Seguro?', required=True),
    }

stock_create_global()
