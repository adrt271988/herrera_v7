# -*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 OpenERP Venezuela (http://openerp.com.ve)
# All Rights Reserved.
# Programmed by: Israel Fermín Montilla  <israel@openerp.com.ve>
#
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
from openerp.osv import osv,fields
from openerp.tools.translate import _
from openerp import pooler
import time
import openerp.addons.decimal_precision as dp

class inherited_stock_move(osv.osv):

    _inherit = "stock.move"

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        res = super(inherited_stock_move, self).create(
            cr, uid, vals, context=context)
        #~ print '******* vals *********',vals
        return  res

inherited_stock_move()

class inherited_stock_inventory(osv.osv):

    _inherit = "stock.inventory"
    
    def _get_shop_by_location(self, cr, uid, location_id, context = None):
        shp_id = False
        wrh_id = location_id and self.pool.get('stock.warehouse').search(cr, uid, ['|','|',('lot_input_id','=',location_id),('lot_stock_id','=',location_id),('lot_output_id','=',location_id)]) or False
        if not wrh_id:
            # si esta locacion pertenece a un encadenamiento tomamos como padre a su encadenado superior
            parent = self.pool.get('stock.location').search(cr, uid, [('chained_location_id','=',location_id)])
            parent = parent and parent[0] or False
            # si no tiene encadenamiento tomamos como parent a su padre
            parent = parent or self.pool.get('stock.location').browse(cr, uid, location_id).location_id.id 
            shp_id = parent and self._get_shop_by_location(cr, uid, parent) or shp_id
        return shp_id or wrh_id and self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',wrh_id[0])])
    
    def action_done(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        res = super(inherited_stock_inventory, self).action_done(
            cr, uid, ids, context=context)
        # Recorremos las lineas para actualizar el costo promedio
        for inv in self.browse(cr, uid, ids, context=context):
            for mov in inv.move_ids:
                self.pool.get('average.cost').compute_average_cost(cr, uid, mov.id, context=context)
        return res
        
    def action_cancel_inventory(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        res = super(inherited_stock_inventory, self).action_cancel_inventory(
            cr, uid, ids, context=context)
        # Recorremos las lineas para actualizar el costo promedio
        for inv in self.browse(cr, uid, ids, context=context):
            for mov in inv.move_ids:
                self.pool.get('average.cost').compute_average_cost(cr, uid, mov.id, context=context)
        return res  

inherited_stock_inventory()
