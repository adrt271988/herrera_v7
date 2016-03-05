# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta


class inherit_distribution_account_voucher(osv.osv):
    
    _inherit = 'account.voucher'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for rec in self.browse(cr, uid, ids, context):
	    ref = rec.reference and rec.reference or ''
	    res.append((rec.id, rec.number+' | '+ref))
        return res
    
    def button_proforma_voucher(self, cr, uid, ids, context=None):
	res = super(inherit_distribution_account_voucher,self).button_proforma_voucher(cr, uid, ids, context=context)
	if context.get('moves'): ### Colocamos los moves relacionados al pedido en done
	    inv_pool = self.pool.get('account.invoice')
	    invoice_id = context['active_id']
	    invoice = inv_pool.browse(cr, uid, invoice_id, context)
	    if invoice.state == 'paid':
		if invoice.reception_type == 'received':
		    self.pool.get('stock.move').action_done(cr, uid, context.get('moves'), context)
		inv_pool.write(cr, uid, [invoice_id], {'reception_progress':'done'})
	return {'type': 'ir.actions.act_window_close'}

    _columns = {
		    'partner_bank_id': fields.many2one('res.partner.bank', 'Cuenta Bancaria Cliente'),
		}

inherit_distribution_account_voucher()
