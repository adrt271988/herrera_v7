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

class stock_distribution_report(report_sxw.rml_parse):
    _name = 'report.stock.distribution.report'
    
    def __init__(self, cr, uid, name, context):
        super(stock_distribution_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
	    'get_date': self._get_date,
            'get_routes': self._get_routes,
            'get_lines': self._get_lines,
            'get_sums': self._get_sums,
            'get_total': self._get_total,
        })
        self.context = context

    def _get_date(self, date):
	date_string = date.split(" ")
        date_substr = date_string[-1].split(".")
        date_string[-1] = date_substr[0]
        date_string = " ".join(date_string)
	return date_string
    
    def _get_routes(self,distro,data):
        res = []
        route_obj = self.pool.get('freight.route')
        self.cr.execute(""" SELECT f.id, f.name, f.rank, s.name AS sucursal, l.distro_id, dr.driver_type FROM stock_distribution_line l
                                JOIN freight_route f ON f.id = l.route_id
                                JOIN sale_shop s ON s.id = f.shop_id
                                JOIN stock_distribution d ON d.id = l.distro_id
                                JOIN fleet_drivers dr ON dr.id = d.driver_id
                                WHERE l.distro_id = %s
                                GROUP BY f.id, f.name, f.rank, sucursal, l.distro_id, dr.driver_type
                                ORDER BY f.id"""%(distro.id))
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

    def _get_lines(self,routes,data):
        self.cr.execute(""" SELECT *, s.name AS sale, s.date_order, p.name AS partner FROM stock_distribution AS d
                                JOIN stock_distribution_line AS line ON line.distro_id = d.id
                                JOIN sale_order AS s ON line.sale_id = s.id
                                JOIN res_partner AS p ON line.partner_id = p.id
                                WHERE d.id = %s AND line.route_id = %s """%(routes.get('distro_id'),routes.get('id')))
        resul = self.cr.dictfetchall()
        return resul

    def _get_sums(self,routes,data):
        route_id = routes.get('id')
        self.cr.execute(""" SELECT SUM(line.product_qty) AS total_qty, SUM(line.weight) AS total_weight,
                                    SUM(line.volume) AS total_volume, SUM(line.payment_independent_units) AS total_piu
                                FROM stock_distribution AS d
                                JOIN stock_distribution_line AS line ON line.distro_id = d.id
                                WHERE d.id = %s AND line.route_id = %s """%(routes.get('distro_id'),route_id))
        resul = self.cr.dictfetchall()
        return resul

    def _get_total(self,distro,data):
        self.cr.execute(""" SELECT SUM(line.product_qty) AS total_qty, SUM(line.weight) AS total_weight,
                                    SUM(line.volume) AS total_volume, SUM(line.payment_independent_units) AS total_piu
                                FROM stock_distribution AS d
                                JOIN stock_distribution_line AS line ON line.distro_id = d.id
                                WHERE d.id = %s"""%(distro.id))
        resul = self.cr.dictfetchall()
        vol_capacity = distro.vehicle_id.volumetric_capacity and distro.vehicle_id.volumetric_capacity or False
        resul[0]['kgs_percent'] = float(resul[0]['total_weight']*100) / float(distro.vehicle_id.capacity_kgs)
        resul[0]['vol_percent'] = vol_capacity and float(resul[0]['total_volume']*100) / float(distro.vehicle_id.volumetric_capacity) or 0.00
        return resul

report_sxw.report_sxw('report.stock.distribution.report','stock.distribution', parser=stock_distribution_report,header=False, rml='herrera_distribution/report/stock_distribution_report.rml')
