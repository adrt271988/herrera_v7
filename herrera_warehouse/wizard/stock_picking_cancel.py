# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class stock_picking_cancel(osv.osv_memory):
    _name = "stock.picking.cancel"

    def stock_picking_cancel(self, cr, uid, ids, context = None):
        if context is None:
            context = {}

        active = {'ids' : context.get('active_ids', [False])}
        picking_ids = active.get('ids')
        self.pool.get('stock.picking').action_cancel(cr, uid, picking_ids, context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
                    'sure' :fields.boolean('Seguro?', required=True),
                }

stock_picking_cancel()
