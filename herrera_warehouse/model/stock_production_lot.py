# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from openerp import netsvc
from datetime import datetime,time
from openerp import tools
from openerp.osv import osv,fields
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

def str_to_datetime(strdate):
    return datetime.strptime(strdate, tools.DEFAULT_SERVER_DATE_FORMAT)


class stock_production_lot(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for rec in self.browse(cr, uid, ids, context):
            if rec.product_id:
                product = self.pool.get('product.product').browse(cr, uid, rec.product_id.id, context)
                pvm = rec.pvm and rec.pvm or 0.00
                use_date = rec.use_date and rec.use_date[0:10].split('-')
                use_date = use_date and '%s/%s/%s'%(use_date[2],use_date[1],use_date[0]) or '****N/A****'
                name = 'No. %s | FV: %s |  PVM: %s'%(rec.name.zfill(10),use_date,(str(pvm)))
                res.append((rec.id, name))
        return res

    def default_get(self, cr, uid, fields_list, context=None):
        context = context and context or {}
        res = super(stock_production_lot, self).default_get(cr, uid, fields_list, context)
        product_id = res.get('product_id',False)
        if product_id:
            pvm = self.pool.get('product.product').browse(cr, uid, product_id, context).pvm
            res.update({'pvm': pvm and pvm or 0.00})
        return res

    def onchange_product_id(self, cr, uid, ids, product_id):
        res = {'value': {}}
        if product_id:
            pvm = self.pool.get('product.product').browse(cr, uid, product_id).pvm
            res['value'].update({'pvm': pvm and pvm or 0.00})
        return res

    _inherit = 'stock.production.lot'
    _order = 'use_date desc'
    _columns = {
        'name': fields.char('Serial Number', size=40, required=True, help="Unique Serial Number, will be displayed as: PREFIX/SERIAL [INT_REF]"),
        'pvm' : fields.float('Precio de Venta Marcado', help = "Precio de Venta Marcado del Producto"),
    }
    
    def onchange_use_date(self, cr, uid, ids, use_date):
        res = {}
        life_date = use_date and datetime.strftime((str_to_datetime(use_date[0:10]) + relativedelta(months=4)), tools.DEFAULT_SERVER_DATE_FORMAT)+use_date[10:] or use_date
        removal_date = use_date and datetime.strftime((str_to_datetime(use_date[0:10]) + relativedelta(months=5)), tools.DEFAULT_SERVER_DATE_FORMAT)+use_date[10:] or use_date
        alert_date = use_date and datetime.strftime((str_to_datetime(use_date[0:10]) - relativedelta(months=1)), tools.DEFAULT_SERVER_DATE_FORMAT)+use_date[10:] or use_date
        value = {'life_date': life_date, 'removal_date': removal_date, 'alert_date': alert_date }
        res.update({'value': value}) 
        return res
    
stock_production_lot()
