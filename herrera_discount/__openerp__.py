# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Unknown (<openerp@suniagajose-HN-70>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

{
    'name': "Descuentos Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    'category':  "Modulos de Herrera",
    'description': """ 
    Este módulo contiene las estructuras basicas para crear descuentos en facturas para ser aplicado desde ordenes de compras, ventas y servicios.
    """,
    "depends": ['herrera_sales', 'herrera_fleet', 'herrera_purchase'],
    "data": [
        "security/ir.model.access.csv",
        "view/purchase_view.xml",
        "view/discount_view.xml",
    ],
    "demo_xml": [],
    "test": [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
