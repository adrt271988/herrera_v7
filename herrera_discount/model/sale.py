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

class inherited_sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'discount_ids': fields.one2many('sale.order.discount', 'order_id', 'Descuentos en factura', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'credit_except': [('readonly', False)]}),
    }
inherited_sale_order()

class sale_order_discount(osv.osv):
    _name = "sale.order.discount"
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            cur = line.order_id.pricelist_id.currency_id
            total = line.order_id.amount_untaxed
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res
        
    _columns = {
        'order_id': fields.many2one('sale.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'name': fields.char('Name', size=256, required=True),
        'discount_id': fields.many2one('discount', 'Discount', domain=[('order_type', '=', 'sale')], change_default=True),
        'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount'), readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }
sale_order_discount()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
