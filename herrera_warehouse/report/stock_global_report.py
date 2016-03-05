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

class stock_global_report(report_sxw.rml_parse):
    _name = 'report.stock.global.report'
    
    def __init__(self, cr, uid, name, context):
        super(stock_global_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_date': self._get_date,
            'get_lines': self._get_lines,
        })
        self.context = context

    def _get_date(self, date):
	date_string = date.split(" ")
        date_substr = date_string[-1].split(".")
        date_string[-1] = date_substr[0]
        date_string = " ".join(date_string)
	return date_string

    def _get_lines(self,global_brw,data):
        res = []
        for line in global_brw.global_lines:
            values = {
                        'name' : line.name,
                        'product' : '['+line.product_id.code+']'+' '+line.product_id.name+' '+line.product_id.pack,
                        'product_qty' : line.product_qty,
                        'uom' : line.uom_id.name,
                        'weight' : line.weight,
                        'volume' : line.volume,
                        'supplier_code' : line.supplier_code,
                        'palette': line.palette,
                        }
            res.append(values)
        return res

report_sxw.report_sxw('report.stock.global.report','stock.global', parser=stock_global_report,header=False, rml='herrera_warehouse/report/stock_global_report.rml')
