# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_payment_condition(osv.osv):

    _name = 'account.payment.condition'
        
    _columns = {
                 'name': fields.char('Nombre', size=32, required= True),
                 'code': fields.char('Código', size=1),
                 'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the payment condition without removing it."),
                 'note': fields.text('Description'),
                 'term_ids': fields.many2many('account.payment.term', 'account_payment_term_condi_rel', 'condi_id', 'term_id', 'Plazos de Pago'),
                 'payment_term': fields.many2one('account.payment.term', 'Predeterminado', required=True),
                }

account_payment_condition()
