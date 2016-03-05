# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class stock_picking_confirm(osv.osv_memory):
    _name = "stock.picking.confirm"

    def stock_picking_confirm(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        done = []
        count = 0
        pickings = {}
        wf_service = netsvc.LocalService('workflow')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        active = {'ids' : context.get('active_ids', [False])}
        picking_ids = active.get('ids')
        for pick in picking_ids:
            move_ids = move_obj.search(cr, uid, [('picking_id','=', pick)])
            for move in move_obj.browse(cr, uid, move_ids, context):
                if move.product_id.type == 'consu' or move.location_id.usage == 'supplier':
                    if move.state in ('confirmed', 'waiting'):
                        done.append(move.id)
                    pickings[move.picking_id.id] = 1
                    continue
                if move.state in ('confirmed', 'waiting'):
                    res = self.pool.get('stock.location')._product_reserve(cr, uid, [move.location_id.id], move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                    if res:
                        move_obj.write(cr, uid, [move.id], {'state':'assigned'})
                        done.append(move.id)
                        pickings[move.picking_id.id] = 1
                        r = res.pop(0)
                        product_uos_qty = move_obj.onchange_quantity(cr, uid, ids, move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                        cr.execute('update stock_move set location_id=%s, product_qty=%s, product_uos_qty=%s where id=%s', (r[1], r[0],product_uos_qty, move.id))
                        while res:
                            r = res.pop(0)
                            move_id = move_obj.copy(cr, uid, move.id, {'product_uos_qty': product_uos_qty, 'product_qty': r[0], 'location_id': r[1]})
                            done.append(move_id)
            if done:
                count += len(done)
                move_obj.write(cr, uid, done, {'state': 'assigned'})
            if count:
                for pick_id in pickings:
                    wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
                    #~ self.pool.get('sale.stock.massive.analysis').massive_do_partial(cr, uid, [pick_id], done, context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
                    'sure' :fields.boolean('Seguro?', required=True),
                }

stock_picking_confirm()
