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

class stock_hall_report(report_sxw.rml_parse):
    _name = 'report.stock.hall.report'
    
    def __init__(self, cr, uid, name, context):
        super(stock_hall_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_halls': self._get_halls,
            'get_halls_lines': self._get_halls_lines,
        })
        self.context = context

    def _get_halls(self,global_obj, data):
        query= []
        for glo in global_obj:
            query = self.cr.execute(''' SELECT * FROM stock_hall_document WHERE global_id = %s ORDER BY name ASC'''% (glo.id))
            query = self.cr.dictfetchall()
	    print 'query***************************',query
        return query

    def _get_halls_lines(self,hall, data):
        query = self.cr.execute(''' SELECT line.*, p.product_tmpl_id, p.default_code AS product_code, t.name AS product_name,
                                            l.complete_name AS location_name, u.name AS uom_name, lot.name AS lot_name
                                        FROM stock_hall_document_line AS line
                                        JOIN product_product AS p ON line.product_id = p.id
                                        JOIN product_template AS t ON p.product_tmpl_id = t.id
                                        JOIN product_uom AS u ON line.uom_id = u.id
                                        LEFT JOIN stock_production_lot AS lot ON line.prodlot_id = lot.id
                                        JOIN stock_location AS l ON line.location_id = l.id
                                        WHERE line.hall_id = %s ORDER BY name ASC'''% (hall.get('id')))
        query = self.cr.dictfetchall()
        for q in query:
            split = q['location_name'].split("/")
            q['location_name'] = split[5]+' / '+split[6]
        return query

report_sxw.report_sxw('report.stock.hall.report','stock.global', parser=stock_hall_report,header=False, rml='herrera_warehouse/report/stock_hall_report.rml')
