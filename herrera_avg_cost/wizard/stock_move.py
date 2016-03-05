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
import datetime, time
from openerp.osv import fields, osv
from tools.translate import _

class inherited_stock_move_scrap(osv.osv_memory):
    _inherit = "stock.move.scrap"

    def move_scrap(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        res = super(inherited_stock_move_scrap, self).move_scrap(cr, uid, ids, context)
        # Recorremos las lineas para actualizar el costo promedio
        if res.get('move_ids',[]):
            for move_id in res['move_ids']:
                self.pool.get('average.cost').compute_average_cost(cr, uid, move_id, context=context)
            
inherited_stock_move_scrap()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
