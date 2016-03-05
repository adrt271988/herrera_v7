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

class products_outside_stock(report_sxw.rml_parse):
    _name = 'report.products.outside.stock'
    
    def __init__(self, cr, uid, name, context):
        super(products_outside_stock, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_header': self._get_header,
            'get_lines': self._get_lines,
        })
        self.context = context

    def _get_header(self,data):
	product = self.pool.get('product.product')
	res = []
	for d in data['form'].keys():
	    product_id = int(d)
	    product_brw = product.browse(self.cr, self.uid, product_id)
	    product_name = '['+product_brw.default_code+'] '+product_brw.name
	    res.append({'product_id': product_id, 'product_name': product_name, 'qty_missing': float(data['form'][d])})
	return res
	
    def _get_lines(self,data,header):
	res = []
	self.cr.execute(""" SELECT move.product_qty, p.default_code AS product_code, t.name AS product_name,
				loca.complete_name AS location_name, u.name AS uom_name, lot.name AS lot_name
			FROM stock_move AS move
			JOIN stock_picking AS pick ON pick.id = move.picking_id
			JOIN product_product AS p ON move.product_id = p.id
			JOIN product_template AS t ON p.product_tmpl_id = t.id
			LEFT JOIN stock_production_lot AS lot ON lot.id = move.prodlot_id
			JOIN stock_location as loca ON loca.id = move.location_dest_id
			JOIN product_uom AS u ON t.uom_id = u.id
			WHERE move.product_id = %s
			AND pick.type = 'internal'
			AND move.state = 'done'
			AND loca.usage = 'internal'
			AND loca.chained_location_type <> 'customer'
			AND loca.level < 6
			"""%(header['product_id']))
	res = self.cr.dictfetchall()
        for r in res:
	    split = r['location_name'].split("/")
	    split.pop(0)
	    cadena = ''
	    for i in split:
		cadena += i+'/'
	    r['location_name'] = cadena
        return res

report_sxw.report_sxw('report.products.outside.stock','sale.order', parser=products_outside_stock,header=False, rml='herrera_sales/report/products_outside_stock.rml')
