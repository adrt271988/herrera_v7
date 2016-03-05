# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler
from datetime import datetime

class invoice_forwarding_report(report_sxw.rml_parse):
    _name = 'report.invoice.forwarding.report'
    
    def __init__(self, cr, uid, name, context):
        super(invoice_forwarding_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
	    'get_date': self._get_date,
            'get_invoice': self._get_invoice,
            'get_lines': self._get_lines,
        })
        self.context = context

    def _get_date(self, date):
	date_string = date.split(" ")
        date_substr = date_string[-1].split(".")
        date_string[-1] = date_substr[0]
        date_string = " ".join(date_string)
	return date_string

    def _get_invoice(self, reception):
	res = []
	inv = [x.id for x in reception.invoice_ids if (x.reception_type in ['resent'])]
	if inv:
	    res = self.pool.get('account.invoice').read(self.cr, self.uid, inv, ['number'])
	return res

    def _get_lines(self, invoice_id):
	res = []
	if invoice_id:
	    self.cr.execute(''' select p.default_code, t.name, l.quantity from account_invoice i
				    join account_invoice_line as l on l.invoice_id = i.id
				    join product_product as p on p.id = l.product_id
				    join product_template as t on t.id = p.product_tmpl_id
				    where i.id = %s'''%invoice_id)
	    res = self.cr.dictfetchall()
	return res

report_sxw.report_sxw('report.invoice.forwarding.report','stock.reception', parser=invoice_forwarding_report,header=False, rml='herrera_distribution/report/invoice_forwarding_report.rml')
