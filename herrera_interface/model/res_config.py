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

class interface_config_settings(osv.osv_memory):
    _name = 'interface.config.settings'
    _inherit = 'res.config.settings'
    _columns = {
        'import_path': fields.char('Import path', size=128, help="Path for import txt files"),
        'export_path': fields.char('Export path', size=128, help="Path for export txt files"),
    }
    
        
    def get_default_interface_path(self, cr, uid, fields, context=None):
        imp = self.pool.get("ir.config_parameter").get_param(cr, uid, "herrera_interface.import_path") or ""
        exp = self.pool.get('ir.config_parameter').get_param(cr, uid, "herrera_interface.export_path") or ""
        return {'import_path': imp, 'export_path': exp,}
    
    def set_default_interface_path(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        icp = self.pool.get('ir.config_parameter')
        # we store the repr of the values, since the value of the parameter is a required string
        icp.set_param(cr, uid, 'herrera_interface.import_path', config.import_path)
        icp.set_param(cr, uid, 'herrera_interface.export_path', config.export_path)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
