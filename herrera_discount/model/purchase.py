# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _

import openerp.addons.decimal_precision as dp

class inherited_purchase_order(osv.osv):
    _inherit = "purchase.order"
        
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_discount': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'discount': 0.0,
            }
            dsc = dsc1 = 1.0
            val = val1 = val2 = 0.0
            cur = order.pricelist_id.currency_id
            for purchase_discount in order.discount_ids:
                dsc1 *= (1.0-purchase_discount.discount/100.0)
            dsc = ( dsc - dsc1 ) * 100.0
            for line in order.order_line:
                val1 += line.price_subtotal
                c = self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit * dsc1, line.product_qty, line.product_id, order.partner_id)['taxes']
                val += c and c[0].get('amount', 0.0) or 0.0
            res[order.id]['discount'] = dsc
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            val2 += res[order.id]['amount_untaxed'] * ( (dsc or 0.0) / 100.0 )
            res[order.id]['amount_discount']=cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] - res[order.id]['amount_discount'] + res[order.id]['amount_tax']
        return res
         
    def _get_order_from_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
         
    def _get_order_from_discount(self, cr, uid, ids, context=None):
        result = {}
        for discount in self.pool.get('purchase.order.discount').browse(cr, uid, ids, context=context):
            result[discount.order_id.id] = True
        return result.keys()

    _columns = {
        'discount_ids': fields.one2many('purchase.order.discount', 'order_id', 'Descuentos en factura'),
        'discount':fields.function(_amount_all, type='float', string='Descuento en factura (%)', 
            store={ 
                'purchase.order.discount':(_get_order_from_discount, None, 10) 
            }, multi="sums", digits=(12, 4), help="Porcentaje de descuento aplicado sobre la base imponible de la factura"),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order_from_line, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_discount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Descuentos',
            store={
                'purchase.order.discount':(_get_order_from_discount, None, 10),
                'purchase.order.line': (_get_order_from_line, None, 10),
            }, multi="sums", help="The discount amount on invoice"),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.discount':(_get_order_from_discount, None, 10),
                'purchase.order.line': (_get_order_from_line, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.discount':(_get_order_from_discount, None, 10),
                'purchase.order.line': (_get_order_from_line, None, 10),
            }, multi="sums",help="The total amount"),
    }
inherited_purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
