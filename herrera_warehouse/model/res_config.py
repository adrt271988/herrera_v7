# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

from openerp.osv import fields, osv

class inherited_stock_config_settings(osv.osv_memory):
    _inherit = 'stock.config.settings'
    
    _columns = {
        'stock_production_lot': fields.boolean("Forzar número de serie en las recepciones",
            help="""Impide recepcionar producto sin numero de serie"""),
    }
    
    def get_default_stock_production_lot(self, cr, uid, fields, context=None):
        search_ids = self.search(cr, uid, [])
        last_id = search_ids and max(search_ids) or False
        return {'stock_production_lot': last_id and self.browse(cr, \
                        uid, last_id, context).stock_production_lot }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
