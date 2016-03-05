# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _


class inherited_partner(osv.osv):

    _inherit = 'res.partner'
        
    def onchange_payment_condition(self, cr, uid, ids, payment_condition, supplier=False, context=None):
        if context is None: context = {}
        domain = {}
        value = {}
        if payment_condition:
            condition_brw = self.pool.get('account.payment.condition').browse(cr, uid, payment_condition)
            term_ids = map(lambda x : x.id, condition_brw.term_ids)
            if supplier:
                domain = {'property_supplier_payment_term': [('id','in',term_ids)]}
                value = {'property_supplier_payment_term': condition_brw.payment_term.id or False }
            else:
                domain = {'property_payment_term': [('id','in',term_ids)]}
                value = {'property_payment_term': condition_brw.payment_term.id or False }
        
        return {'value': value, 'domain': domain}

    _columns = {
       'payment_condition': fields.many2one('account.payment.condition', 'Payment Condition'),
       'supplier_payment_condition': fields.many2one('account.payment.condition', 'Supplier Payment Condition'),
   }

inherited_partner()
