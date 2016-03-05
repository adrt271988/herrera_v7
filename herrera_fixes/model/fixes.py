# -*- coding: utf-8 -*-
from osv import osv, fields
import decimal_precision as dp
import netsvc
import pooler

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"
    
    def _get_journal_id(self, cr, uid, context=None):
        print "context['default_type']",context['default_type']
        ctx = context
        if ctx.get('active_model',False):
            ctx['active_model'] = []
        result = super(stock_invoice_onshipping,self)._get_journal_id(cr, uid, ctx)
        
        model = context.get('active_model')
        if not model or 'stock.picking' not in model:
            return []

        model_pool = self.pool.get(model)
        journal_obj = self.pool.get('account.journal')
        res_ids = context and context.get('active_ids', [])
        vals = []
        browse_picking = model_pool.browse(cr, uid, res_ids, context=context)

        for pick in browse_picking:
            if not pick.move_lines:
                continue
            src_usage = pick.move_lines[0].location_id.usage
            dest_usage = pick.move_lines[0].location_dest_id.usage
            #~ print "context['default_type']",context['default_type']
            type = context['default_type']
            if type == 'out' and dest_usage == 'supplier':
                journal_type = 'purchase_refund'
            elif type == 'out' and dest_usage == 'customer':
                journal_type = 'sale'
            elif type == 'in' and src_usage == 'supplier':
                journal_type = 'purchase'
            elif type == 'in' and src_usage == 'customer':
                journal_type = 'sale_refund'
            else:
                journal_type = 'sale'

            value = journal_obj.search(cr, uid, [('type', '=',journal_type )])
            for jr_type in journal_obj.browse(cr, uid, value, context=context):
                t1 = jr_type.id,jr_type.name
                if t1 not in vals:
                    vals.append(t1)
        return vals

stock_invoice_onshipping()
