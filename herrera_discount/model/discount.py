# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Unknown (<openerp@suniagajose-HN-70>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

class discount(osv.osv):

    _name = "discount"
    _description = "Descuentos para ordenes de venta/compra/servicio"
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(discount,self).default_get(cr, uid, fields, context=context) 
        if 'order_type' in context:
            res.update({'order_type': context['order_type']})
        return res
        
    _columns = {
        'name': fields.char('Nombre', size=256, required=True, select=True),
        'order_type': fields.selection([
            ('sale', 'Pedido de Venta'),
            ('purchase', 'Pedido de Compra'),
            ('service', 'Orden de Servicio'),
            ], 'Documento', required=True, help="El documento seleccionado será en donde se podrá utilizar este descuento"),
        'value': fields.float('Descuento (%)', digits_compute=dp.get_precision('Discount'), help="Representa el valor porcentual del descuento"),
        'note': fields.text('Descripcion', help="Explicación sobre cuando y como se aplica este descuento, si posee algun tipo de condicion especial, etc."),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the payment condition without removing it."),

        }
        
    _defaults = {
        'active' : True,
    }

discount()

class purchase_order_discount(osv.osv):
    _name = "purchase.order.discount"
    _order = "order_id,sequence"
        
    def discount_id_change(self, cr, uid, ids, discount_id):
        res = {}
        if discount_id:
            discount = self.pool.get('discount').browse(cr, uid, discount_id)
            res.update({'value': { 'name': '%s (%s%%)'%(discount.name,discount.value), 'discount': discount.value } })
        return res
        
    def discount_value_change(self, cr, uid, ids, discount_id, value):
        res = {}
        if discount_id:
            discount = self.pool.get('discount').browse(cr, uid, discount_id)
            res.update({'value': { 'name': '%s (%s%%)'%(discount.name,value) } })
        return res
        
    _columns = {
        'order_id': fields.many2one('purchase.order', 'Order Reference', required=True, ondelete='cascade', select=True ),
        'name': fields.char('Name', size=256, required=True),
        'discount_id': fields.many2one('discount', 'Discount', domain=[('order_type', '=', 'purchase')], change_default=True),
        'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount') ),
        'sequence': fields.integer('Secuencia', help="Orden de prioridad en la que sera aplicado el descuento al monto bruto"),
    }
    
    _defaults = {
        'sequence': 1,
    }
    
purchase_order_discount()
