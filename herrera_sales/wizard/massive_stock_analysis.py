# -*- encoding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
from openerp.tools.float_utils import float_compare
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class sale_stock_massive_analysis(osv.osv_memory):

    _name = 'sale.stock.massive.analysis'

    def default_get(self, cr, uid, fields_list, context=None):
        context = context and context or {}
        ids = []
        res = super(sale_stock_massive_analysis, self).default_get(cr, uid, fields_list, context)
        if 'active_ids' in context:
            ids = context['active_ids']
        for sale_brw in self.pool.get('sale.order').browse(cr, uid, ids, context):
            if sale_brw.state not in ['draft','sent','approved','credit_except']:
                 raise osv.except_osv(_(u'Acción incorrecta!'), _(u'Este proceso se aplica sólo a pedidos sin confirmar!\n\n Ayuda:\n Vaya a menú "Presupuestos"'))
        return res
        
    def onchange_check_stock(self, cr, uid, ids, check_stock, product_reserve, context = None):
        if not check_stock:
            return {'value': {'product_reserve': False} }
        return True

    def onchange_product_reserve(self, cr, uid, ids, product_reserve, context = None):
        return {'value': {'check_stock': product_reserve and True or False} }
    
    def sale_order_analysis(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context)
        sale_obj = self.pool.get('sale.order')
        active = {'ids' : context.get('active_ids', [False])}
        sale_ids = active.get('ids')
        if not wizard.check_stock and not wizard.product_reserve and not wizard.credit_test:
            raise osv.except_osv(_('Error!'), _('Seleccione alguna opción para continuar'))
        if wizard.credit_test:
            for sale_brw in sale_obj.browse(cr, uid, sale_ids, context):
                sale_obj.action_button_approved(cr, uid, [sale_brw.id], context=context)
        if wizard.check_stock:
            for sale_brw in sale_obj.browse(cr, uid, sale_ids, context):
                sale_obj.check_outside_stock(cr, uid, [sale_brw.id], context=context)
        if wizard.product_reserve:
            for sale_brw in sale_obj.browse(cr, uid, sale_ids, context):
                if sale_brw.state == 'approved':
                    sale_obj.check_product_reserve(cr, uid, [sale_brw.id],context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'product_reserve' :fields.boolean('Reservar Productos'),
        'credit_test' :fields.boolean('Analisis Crediticio'),
        'check_stock' :fields.boolean('Analisis de Disponibilidad'),
    }

sale_stock_massive_analysis()
