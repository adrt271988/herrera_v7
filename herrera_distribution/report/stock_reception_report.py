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

class stock_reception_report(report_sxw.rml_parse):
    _name = 'report.stock.reception.report'
    
    def __init__(self, cr, uid, name, context):
        super(stock_reception_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
	    'get_date': self._get_date,
            'get_routes': self._get_routes,
            'get_lines': self._get_lines,
            'get_refund_lines': self._get_refund_lines,
            'get_total': self._get_total,
        })
        self.context = context

    def _get_date(self, date):
	date_string = date.split(" ")
        date_substr = date_string[-1].split(".")
        date_string[-1] = date_substr[0]
        date_string = " ".join(date_string)
	return date_string
    
    def _get_routes(self,reception,data):
        res = []
        route_obj = self.pool.get('freight.route')
        self.cr.execute(""" SELECT f.id, f.name, f.rank, s.name AS sucursal, l.distro_id, dr.driver_type FROM stock_distribution_line l
                                JOIN freight_route f ON f.id = l.route_id
                                JOIN sale_shop s ON s.id = f.shop_id
                                JOIN stock_distribution d ON d.id = l.distro_id
                                JOIN fleet_drivers dr ON dr.id = d.driver_id
                                WHERE l.distro_id = %s
                                GROUP BY f.id, f.name, f.rank, sucursal, l.distro_id, dr.driver_type
                                ORDER BY f.id"""%(reception.distribution_id.id))
        resul = self.cr.dictfetchall()
        for i in resul:
            route_id = i.get('id')
            for d in route_obj.browse(self.cr, self.uid, route_id).detail_ids:
                if i.get('driver_type') == 'C':
                    if d.type == 'CC':
                        i.update({'rate_weight':d.weight, 'rate_volume': d.volume, 'rate_boxes': d.boxes})
                else:
                    if d.type == 'CF':
                        i.update({'rate_weight':d.weight, 'rate_volume': d.volume, 'rate_boxes': d.boxes})
        return resul
    
    def _get_lines(self,reception,routes):
	resul = []
	inv_pool = self.pool.get('account.invoice')
        self.cr.execute(""" SELECT r.*, i.number, i.id AS invoice_id, i,reception_type, i.date_invoice, i.amount_total, p.name AS partner FROM stock_reception AS r
                                JOIN account_invoice AS i ON r.id = i.reception_id
                                JOIN res_partner AS p ON i.partner_id = p.id
                                WHERE r.id = %s AND p.freight_route_id = %s AND i.reception_type in ('partial_refund','received') """%(reception.id,routes.get('id')))
        resul = self.cr.dictfetchall()
	for inv in resul:
	    inv_qty = 0.00
	    inv_weight = 0.00
	    check_amount = cash_amount = 0.00
	    inv_brw = inv_pool.browse(self.cr, self.uid, inv['invoice_id'])
	    ### Calculamos udv y kgs totales por cada factura
	    for line in inv_brw.invoice_line:
		inv_weight += line.quantity*line.product_id.weight
		inv_qty += line.quantity
	    ### Obtenemos los pagos de la factura
	    if inv_brw.payment_ids:
		check_amount = sum([p.credit for p in inv_brw.payment_ids if (p.journal_id.type == 'bank')])
		cash_amount = sum([p.credit for p in inv_brw.payment_ids if (p.journal_id.type != 'bank')])
	    ### Actualizamos valores del diccionario de la linea de reporte (factura)
	    inv.update({
			'invoice_qty':inv_qty,
			'invoice_weight': inv_weight,
			'reception_date': inv_brw.date_document and inv_brw.date_document or inv_brw.date_invoice,
			'check_amount': check_amount,
			'cash_amount': cash_amount,
			'payment_amount': check_amount + cash_amount,
			})
        return resul

    def _get_refund_lines(self,reception,routes):
	resul = []
	invoice_ids = map(lambda x: x.id, reception.invoice_ids)
	self.cr.execute(""" SELECT i.id FROM account_invoice AS i
                                JOIN res_partner AS p ON i.partner_id = p.id
				WHERE p.freight_route_id = %s
				AND i.parent_id IN %s
				"""%(routes['id'],tuple(invoice_ids)))
	res = self.cr.dictfetchall()
	for child in res:
	    refund = self.pool.get('account.invoice').browse(self.cr, self.uid, child['id'])
	    if refund.parent_id.reception_type == 'partial_refund':
		### Calculamos udv y kgs totales por cada N/C
		inv_qty = 0.00
		inv_weight = 0.00
		for line in refund.invoice_line:
		    inv_weight += line.quantity*line.product_id.weight
		    inv_qty += line.quantity
		resul.append({
				'parent': refund.parent_id.number,
				'amount_total': refund.amount_total,
				'invoice_qty':inv_qty,
				'invoice_weight': inv_weight,
				'reception_date': refund.date_document and refund.date_document or refund.date_invoice,
			    })
	return resul

    def _get_total(self,reception,data):
        resul = []
	invoice_ids = map(lambda x: x.id, reception.invoice_ids)
	total_w = total_q = total_ref_w = total_ref_q = 0.00
	count_refund = 0
	count_received = 0
	for inv in self.pool.get('account.invoice').browse(self.cr, self.uid, invoice_ids):
	    if inv.reception_type in ('partial_refund','received'):
		### Calculamos udv y kgs totales de la recepcion (incluidas N/C)
		inv_weight = inv_qty = 0.00
		for line in inv.invoice_line:
		    inv_weight += line.quantity*line.product_id.weight
		    inv_qty += line.quantity
		total_w += inv_weight
		total_q += inv_qty
		### Calculamos totales de udv y kgs de las N/C
		ref_weight = ref_qty = 0.00
		if inv.child_ids:
		    for refund in inv.child_ids:
			count_refund += 1
			for line in refund.invoice_line:
			    ref_weight += line.quantity*line.product_id.weight
			    ref_qty += line.quantity
		    total_ref_w += ref_weight
		    total_ref_q += ref_qty
		count_received += 1
	resul.append({
			'received_weight': total_w,
			'received_qty': total_q,
			'count_inv': int(count_received),
			'refund_weight': total_ref_w,
			'refund_qty': total_ref_q,
			'count_refund': count_refund,
			'weight': total_w - total_ref_w,
			'qty': total_q - total_ref_q,
			'invoices': int(count_received) + int(count_refund),
			'driver_amount': reception.driver_amount,
		    })
        return resul

report_sxw.report_sxw('report.stock.reception.report','stock.reception', parser=stock_reception_report,header=False, rml='herrera_distribution/report/stock_reception_report.rml')
