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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class inherited_stock_move_scrap(osv.osv_memory):
    _inherit = "stock.move.scrap"
    
    def _get_qty(self,cr,uid,ids,field,arg,context=None):

        brw = self.browse(cr, uid, ids)
        res = {}
        for b in brw:
            res[b.id] = 0.0
        return res

    _columns = {
        'deduce': fields.boolean('Deducir'),
        'qty_available': fields.function(_get_qty, type='float', string='Real Stock'),
        'move_qty': fields.function(_get_qty, type='float', string='Cantidad en albarán'),
        'final_qty': fields.function(_get_qty, type='float', string='Cantidad definitiva'),
        'location_src_id': fields.many2one('stock.location', 'Ubicacion origen', required=True),
        'picking_type': fields.char('Tipo', size=8),
    }
    
    def apply_deduce(self, cr, uid, ids, move_qty, quantity):
        return {'value': {'final_qty': (move_qty - quantity)}}
    
    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: default values of fields
        """
        if context is None:
            context = {}
        res = super(inherited_stock_move_scrap, self).default_get(cr, uid, fields, context=context)
        if 'active_id' in context:
            active_model = context.get('active_model',False)
            if active_model == 'stock.move':
                brw = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            elif active_model == 'stock.inventory.line':
                brw = self.pool.get('stock.inventory.line').browse(cr, uid, context['active_id'], context=context)
            else:
                return res
            # creamos una copia del context y agregamos la ubicacion origen
            # para capturar el qty_available del producto en esa ubicacion
            c = (context or {}).copy()
            c['location'] = brw.location_id.id
            if 'qty_available' in fields:
                res.update({'qty_available':self.pool.get('product.product').browse(cr, uid, brw.product_id.id, context=c).qty_available})
            if 'move_qty' in fields:
                res.update({'move_qty': brw.product_qty})
            if 'product_qty' in fields:
                res.update({'product_qty': 0.0})
            if 'location_src_id' in fields:
                res.update({'location_src_id': c['location']})
            if 'picking_type' in fields:
                res.update({'picking_type': hasattr(brw,'picking_id') and hasattr(brw.picking_id,'type') and brw.picking_id.type})
        return res

    def move_scrap(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        move_ids = []
        if context is None:
            context = {}
        for data in self.browse(cr, uid, ids):
            context['deduce'] = data.deduce
        if context.get('active_model',False) == 'stock.inventory.line':
            line_obj = self.pool.get('stock.inventory.line')
            line_ids = context['active_ids']
            for data in self.browse(cr, uid, ids):
                move_ids = line_obj.action_scrap(cr, uid, line_ids,
                             data.product_qty, data.location_id.id,
                             context=context)
        else:
            move_ids = context['active_ids']
            super(inherited_stock_move_scrap,self).move_scrap(cr, uid, ids, context=context)

        return {'type': 'ir.actions.act_window_close', 'move_ids': move_ids}

inherited_stock_move_scrap()

class inherited_stock_move_split(osv.osv_memory):
    _inherit = "stock.move.split"
    
    def split_lot(self, cr, uid, ids, context=None):
        return super(inherited_stock_move_split,self).split_lot(cr, uid, ids, context=context)

    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into serial numbers

        :param move_ids: the ID or list of IDs of stock move we want to split
        """
        if context is None:
            context = {}
        assert context.get('active_model') == 'stock.move',\
             'Incorrect use of the stock move split wizard'
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                total_move_qty = 0.0
                for line in lines:
                    quantity = line.quantity
                    total_move_qty += quantity
                    if total_move_qty > move_qty:
                        raise osv.except_osv(_('Processing Error!'), _('Serial number quantity %d of %s is larger than available quantity (%d)!') \
                                % (total_move_qty, move.product_id.name, move_qty))
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        self.pool.get('stock.move').log(cr, uid, move.id, _('Unable to assign all lots to this move!'))
                        return False
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': move.product_id.id},
                        context=context)

                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state, 'to_refund':line.to_refund})

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        move_obj.write(cr, uid, [move.id], update_val)
        return new_move
        
inherited_stock_move_split()

class inherited_stock_move_split_lines(osv.osv_memory):
    _inherit = "stock.move.split.lines"
    
    _columns = {
        'to_refund':fields.boolean('Devolver', help= "Marcar para ser devuelta al proveedor"),
    }
    
    _defaults = {
        'to_refund': 0,
    }

inherited_stock_move_split_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
