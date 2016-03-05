# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta


class inherit_distribution_res_partner_bank(osv.osv):
    
    _inherit = 'res.partner.bank'

    def default_get(self, cr, uid, fields_list, context=None):
	context = context and context or {}
	res = super(inherit_distribution_res_partner_bank, self).default_get(cr, uid, fields_list, context)
	partner_id = context.get('partner_id')
	if context.get('partner_id'):
	    res.update({'partner_id':partner_id})
        return res

inherit_distribution_res_partner_bank()
