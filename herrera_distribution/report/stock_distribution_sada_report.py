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

class stock_distribution_sada_report(report_sxw.rml_parse):
    _name = 'report.stock.distribution.sada.report'
    
    def __init__(self, cr, uid, name, context):
        super(stock_distribution_sada_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
	    'get_date': self._get_date,
            'get_partner_sica': self._get_partner_sica,
            'get_tons_sica': self._get_tons_sica,
            'count_inv_sica': self._count_inv_sica,
            'get_products_sica': self._get_products_sica,
            'get_tons_whout_sica': self._get_tons_whout_sica,
	    'get_products_whout_sica': self._get_products_whout_sica,
	    'count_inv_whout_sica': self._count_inv_whout_sica,
        })
        self.context = context

    def _get_date(self, date):
	date_string = date.split(" ")
        date_substr = date_string[-1].split(".")
        date_string[-1] = date_substr[0]
        date_string = " ".join(date_string)
	return date_string
    
    def _get_partner_sica(self,distribution,data):
        res = []
	partner_ids = []
	inv_not_sica = [] ## facturas con clientes sin sica
	### Obtenemos las facturas involucradas en el despacho
        invoice_ids = map(lambda x:x.sale_id.invoice_ids, distribution.line_ids)
	### Obtenemos los partners involucrados en las facturas
	for invoice in invoice_ids:
	    for i in invoice:
		partner_id = i.partner_id.id
		if partner_id not in partner_ids:
		    if i.partner_id.sica_code:
			partner_ids.append(partner_id)
		    else:
			inv_not_sica.append(i.id)
	### Creamos una lista de diccionarios relacionando partner con invoices, a ser usada por las demas funciones del reporte
	if partner_ids:
	    partner_invoices = []
	    for p in partner_ids:
		inv = []
		for invoice in invoice_ids:
		    for i in invoice:
			if i.partner_id.id == p:
			    inv.append(i.id)
		partner_invoices.append({p:inv})
	    data.update({'form':partner_invoices})
	if inv_not_sica:
	    data.update({'whout_sica':inv_not_sica})
	    ### Devolvemos para el ciclo el id y nombre del partner a analizar
	    res = self.pool.get('res.partner').read(self.cr, self.uid, partner_ids, ['name'])
        return res
    
    def _get_tons_sica(self,partner_id,data):
        res = []
	if data.get('form',False):
	    for invoice in data['form']:
		if partner_id in invoice:
		    self.cr.execute(''' select p.sica_id, CAST( s.code AS INTEGER ) AS code,
					    s.name, (SUM(l.quantity*t.weight)/100) as tons_qty from account_invoice as i
					    join account_invoice_line as l on l.invoice_id = i.id
					    join product_product as p on p.id = l.product_id
					    join product_template as t on t.id = p.product_tmpl_id
					    join product_sica as s on p.sica_id = s.id
					    where i.id in %s
					    group by p.sica_id, code, s.name
					    order by code asc''',(tuple(invoice[partner_id]),))
		    res += self.cr.dictfetchall()
	if res:
	    total_tons = sum(map(lambda x: x['tons_qty'], res))
	    res.append({'sica_id':'','code':'','name':'TOTAL','tons_qty':total_tons})
        return res

    def _count_inv_sica(self,partner_id,data):
	res = []
	string = ""
	if data.get('form',False):
	    for inv in data['form']:
		if inv.get(partner_id):
		    inv_numbers = map(lambda x: self.pool.get('account.invoice').browse(self.cr, self.uid, x).number, inv[partner_id])
		    for i in inv_numbers:
			string += i+', '
		    res.append({'count':string})
	return res

    def _get_products_sica(self,partner_id,data):
        sql = []
	res = []
	if data.get('form',False):
	    for invoice in data['form']:
		if partner_id in invoice:
		    self.cr.execute(''' select CAST( s.code AS INTEGER ) AS code, t.name
					    from account_invoice as i
					    join account_invoice_line as l on l.invoice_id = i.id
					    join product_product as p on p.id = l.product_id
					    join product_template as t on t.id = p.product_tmpl_id
					    join product_sica as s on p.sica_id = s.id
					    where i.id in %s
					    group by code, t.name
					    order by code asc''',(tuple(invoice[partner_id]),))
		    sql += self.cr.dictfetchall()
	if sql:
	    count = 0
	    line = {}
	    for i in range((len(sql)/3)+1):
		if i*3+2 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
			'code2':sql[i*3+1]['code'], 'name2':sql[i*3+1]['name'],
			'code3':sql[i*3+2]['code'], 'name3':sql[i*3+2]['name'],
		    })
		elif i*3+1 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
			'code2':sql[i*3+1]['code'], 'name2':sql[i*3+1]['name'],
		    })
		elif i*3 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
		    })
		res.append(line)
		line = {}
        return res
    
    def _get_tons_whout_sica(self,data):
        res = []
	if data.get('whout_sica',False):
	    self.cr.execute(''' select p.sica_id, CAST( s.code AS INTEGER ) AS code,
				    s.name, (SUM(l.quantity*t.weight)/100) as tons_qty from account_invoice as i
				    join account_invoice_line as l on l.invoice_id = i.id
				    join product_product as p on p.id = l.product_id
				    join product_template as t on t.id = p.product_tmpl_id
				    join product_sica as s on p.sica_id = s.id
				    where i.id in %s
				    group by p.sica_id, code, s.name
				    order by code asc''',(tuple(data['whout_sica']),))
	    res = self.cr.dictfetchall()
	if res:
	    total_tons = sum(map(lambda x: x['tons_qty'], res))
	    res.append({'sica_id':'','code':'','name':'TOTAL','tons_qty':total_tons})
        return res

    def _get_products_whout_sica(self,data):
        sql = []
	res = []
	if data.get('whout_sica',False):
	    self.cr.execute(''' select CAST( s.code AS INTEGER ) AS code, t.name
				    from account_invoice as i
				    join account_invoice_line as l on l.invoice_id = i.id
				    join product_product as p on p.id = l.product_id
				    join product_template as t on t.id = p.product_tmpl_id
				    join product_sica as s on p.sica_id = s.id
				    where i.id in %s
				    group by code, t.name
				    order by code asc''',(tuple(data['whout_sica']),))
	    sql += self.cr.dictfetchall()
	if sql:
	    count = 0
	    line = {}
	    for i in range((len(sql)/3)+1):
		if i*3+2 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
			'code2':sql[i*3+1]['code'], 'name2':sql[i*3+1]['name'],
			'code3':sql[i*3+2]['code'], 'name3':sql[i*3+2]['name'],
		    })
		elif i*3+1 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
			'code2':sql[i*3+1]['code'], 'name2':sql[i*3+1]['name'],
		    })
		elif i*3 < len(sql):
		    line.update({
			'code1':sql[i*3]['code'], 'name1':sql[i*3]['name'],
		    })
		res.append(line)
		line = {}
        return res

    def _count_inv_whout_sica(self,data):
	res = []
	string = ""
	if data.get('whout_sica',False):
	    inv_numbers = map(lambda x: self.pool.get('account.invoice').browse(self.cr, self.uid, x).number, data['whout_sica'])
	    for i in inv_numbers:
		string += i+', '
	    res.append({'count':string})
	return res

report_sxw.report_sxw('report.stock.distribution.sada.report','stock.distribution', parser=stock_distribution_sada_report,header=False, rml='herrera_distribution/report/stock_distribution_sada_report.rml')
