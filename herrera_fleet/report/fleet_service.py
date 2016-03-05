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

class fleet_service(report_sxw.rml_parse):
    _name = 'report.fleet.service'

    def __init__(self, cr, uid, name, context):
        super(fleet_service, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_service_lines': self._get_service_lines,
            'get_total': self._get_total,
            'get_partner': self._get_partner,
        })
        self.context = context

    def _get_service_lines(self,service,data):
        res = []
        for line in service.cost_ids:
            values = {
                        'service_name': line.cost_subtype_id.name,
                        'amount': line.amount,
                        'tax': line.tax,
                        'subtotal': line.subtotal,
                        }
            res.append(values)
        return res

    def _get_partner(self,service,data):
        values = {
                    'logo': service.vehicle_id.partner_id.image,
                    'vat': service.vehicle_id.partner_id.vat,
                    'name': service.vehicle_id.partner_id.name,
                    'phone': service.vehicle_id.partner_id.phone,
                    'email': service.vehicle_id.partner_id.email,
                    'street': service.vehicle_id.partner_id.street,
                    'street2': service.vehicle_id.partner_id.street2,
                    'city': service.vehicle_id.partner_id.city,
                    'state_code':service.vehicle_id.partner_id.state_id.code,
                    'country': service.vehicle_id.partner_id.country_id.name,
                    }

        return values

    def _get_total(self,service,data):
        res = []
        total = 0.00
        tax = 0.00
        subtotal = 0.00
        for line in service.cost_ids:
            total += line.amount
            tax += line.tax
            subtotal += line.subtotal
        res.append({'total':total, 'tax': tax, 'subtotal': subtotal})
        return res

report_sxw.report_sxw('report.fleet.service','fleet.vehicle.log.services', parser=fleet_service,header=False, rml='herrera_fleet/report/fleet_service.rml')
