# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
import time

class account_returned_checks(osv.osv_memory):
    _name = "account.returned.checks"

    def default_get(self, cr, uid, fields_list, context=None):
        context = context and context or {}
        res = super(account_returned_checks, self).default_get(cr, uid, fields_list, context)
        if context:
            res.update({'voucher_id': context['active_id']})
        return res

    _columns = {
            'voucher_id' : fields.many2one('account.voucher', 'Cheque'),
            'motive' : fields.char('Motivo', help="Motivo por el cual es devuelto el cheque"),
            'date' : fields.date('Fecha'),
        }

account_returned_checks()
