# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_payment_term(osv.osv):
    
    _inherit = "account.payment.term"

    _columns = {
        'condition_ids': fields.many2many('account.payment.condition', 'account_payment_term_condi_rel', 'term_id', 'condi_id', 'Condiciones de Pago'),
    }
    
account_payment_term()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
