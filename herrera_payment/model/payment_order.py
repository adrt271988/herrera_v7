# -*- encoding: utf-8 -*-
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp
import time


class inherited_payment_order(osv.osv):
    """
    Adecuaciones de las ordenes de pago para Herrera C.A
    """
    _inherit = "payment.order"
    
    _columns = {
                'partner_id': fields.many2one('res.partner', string="Beneficiario", required=True, states={'done': [('readonly', True)]}),
                'invo_ids': fields.one2many('account.move.line', 'order_id', 'Lineas de Factura'),
               }
     


inherited_payment_order()

class inherited_invoice_for_order(osv.osv):

    _inherit = "account.move.line"

    _columns = {
                'order_id': fields.many2one('payment.order', 'Orden', required=True, select=True),
               }
               
inherited_invoice_for_order()

class inherit_payment_order_create(osv.osv_memory):
    """
    Herencia del wizard "Seleccionar Facturas" 
    """
    _inherit = "payment.order.create"
    
    def search_entries(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('account.move.line')
        pay_obj = self.pool.get('payment.order')
        
        journal = self.pool.get('account.journal').search(cr, uid, [('type','in',('purchase','purchase_refund','purchase_debit'))], context=context)

        data = self.browse(cr, uid, ids, context=context)[0]
        due_date = data.duedate
        payment = pay_obj.browse(cr, uid, context['active_id'], context=context)

        domain = [('type', '<>', 'out_invoice'),('state', '<>', 'paid'),('date_due', '=', due_date),('journal_id','in',journal), ('partner_id', '=', payment.partner_id.id)]
        invo_ids = inv_obj.search(cr, uid, domain, context=context)
        moves = []
        for i in inv_obj.browse(cr, uid, invo_ids, context=context):
            for j in i.move_id.line_id:
                moves.append(j.id)
        pay_obj.write(cr, uid, context['active_ids'], {'date_scheduled':due_date,'invo_ids': [(6,0,moves)]})
        return {'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order',
                'res_id': context['active_id'],
                'type': 'ir.actions.act_window',
                }
    
    
inherit_payment_order_create()
