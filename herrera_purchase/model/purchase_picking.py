# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler

class inherited_purchase_order_line(osv.Model):
    _name = "purchase.order"
    _inherit = "purchase.order"
    
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates pickings and appropriate stock moves for given order lines, then
        confirms the moves, makes them available, and confirms the picking.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: list of IDs of pickings used/created for the given order lines (usually just one)
        """
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, super(inherited_purchase_order_line,self)._prepare_order_picking(cr, uid, order, context=context))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu'):
                prepare_order_line = super(inherited_purchase_order_line,self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context)
                prepare_order_line.update({'measure':order_line.measure})
                move = stock_move.create(cr, uid, prepare_order_line)
                if order_line.move_dest_id:
                    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)
        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return [picking_id]

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_ids = []
        for order in self.browse(cr, uid, ids):
            picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))

        # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        # one that should trigger the advancement of the purchase workflow.
        # By default we will consider the first one as most important, but this behavior can be overridden.
        return picking_ids[0] if picking_ids else False
