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
import datetime, time
from openerp.osv import fields, osv
from tools.translate import _

class inherit_stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'
    
    def _get_shop_by_location(self, cr, uid, location_id, context = None):
        wrh_input_id = location_id and self.pool.get('stock.warehouse').search(cr, uid, [('lot_input_id','=',location_id)]) or False
        wrh_stock_id = location_id and self.pool.get('stock.warehouse').search(cr, uid, [('lot_stock_id','=',location_id)]) or False
        wrh_output_id = location_id and self.pool.get('stock.warehouse').search(cr, uid, [('lot_output_id','=',location_id)]) or False
        warehouse_id = wrh_input_id or wrh_stock_id or wrh_output_id
        shop_id = False
        if not warehouse_id:
            parent = location_id and self.pool.get('stock.location').browse(cr, uid, location_id).location_id.id or False
            shop_id = parent and self._get_shop_by_location(cr, uid, parent) or shop_id
        return shop_id or warehouse_id and self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',warehouse_id[0])])

    def do_partial(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if ids: 
            super(inherit_stock_partial_picking, self).do_partial(cr, uid, ids, context)
            # Recorremos las lineas para actualizar el costo promedio
            for partial_move in self.browse(cr, uid, ids[0], context=context).move_ids:
                if partial_move.move_id:
                    self.pool.get('average.cost').compute_average_cost(cr, uid, partial_move.move_id.id, context=context)
        return {'type': 'ir.actions.act_window_close'}

inherit_stock_partial_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
