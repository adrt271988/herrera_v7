# -*- encoding: utf-8 -*-
##############################################################################
# Programmed by: Herrera C.A
##############################################################################
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp import pooler
import datetime
import time
import math
import openerp.addons.decimal_precision as dp

class average_cost(osv.osv):
    """
    Herrera average cost behavoiur
    """
    _name = "average.cost"

    def _get_cost(self,cr,uid,ids,field,arg,context=None):
        brw = self.browse(cr, uid, ids)
        res = {}
        for b in brw:
            res[b.id] = (b.quantity > 0.0) and (b.amount / b.quantity) or b.amount
        return res
        
    def whoami(self,obj):
        return type(obj).__name__
        
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
        
    def _get_average_cost(self, cr, uid, product_id, shop_id):
        avgcost_id = self.search(cr, uid, [('product_id','=',product_id),('shop_id','=',shop_id)])
        return avgcost_id and self.browse(cr, uid, avgcost_id[0]).cost \
            or avgcost_id and self.browse(cr, uid, avgcost_id[0]).last_cost \
            or 0.0
            
    def _create_average_cost(self, cr, uid, qty, amount, product_id, shop_id):
        return self.create(cr, uid, { 
                                        'shop_id' : shop_id,
                                        'product_id' : product_id,
                                        'quantity' : qty,
                                        'amount' : amount,
                                        'product_uom' : self.pool.get('product.product').browse(cr, uid, product_id).uom_id.id,
                                        'last_cost' : float (amount / qty),
                                      })
    
    def _update_average_cost(self, cr, uid, qty, amount, product_id, shop_id, substract = False, use_avg_cost = False):
        ok = True
        avgcost_id = self.search(cr, uid, [('product_id','=',product_id),('shop_id','=',shop_id)])
        if avgcost_id:
            avgcost_brw = self.browse(cr, uid, avgcost_id[0])
            amount = use_avg_cost and float ( qty * avgcost_brw.cost ) or amount
            # aseguramos que no queden en negativo ni las cantidades ni los bolivares
            ok = not (substract and (avgcost_brw.quantity - qty < 0 or avgcost_brw.amount - amount < 0) )
            # si todo esta bien procedemos a actualizar el costo promedio
            ok = ok and self.write(cr, uid, avgcost_id, { 
                                'quantity' : avgcost_brw.quantity + (substract and qty*(-1) or qty),
                                'amount' : avgcost_brw.amount + (substract and amount*(-1) or amount),
                                'last_cost': avgcost_brw.cost > 0.0 and avgcost_brw.cost or avgcost_brw.last_cost,
                              })
        else:
            # si el registro con el costo promedio para este producto y 
            # esta sucursal aun no existe, procedemos a crearlo siempre 
            # y cuando la actualizacion suponga una suma y no una resta
            ok = not substract and self._create_average_cost(cr, uid, qty, amount, product_id, shop_id)
        return ok
        
    def compute_average_cost(self, cr, uid, move_id, context=None):
        move = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
        # verificamos de que modelo proviene el llamado a esta funcion
        active_model = context.get('active_model',False)
        # verificamos el picking de este movimiento
        pick_type = hasattr(move.picking_id,'type') and move.picking_id.type
        product_id = move.product_id.id
        uom_id = move.product_uom.id
        qty = move.product_qty
        amount = move.price_unit and float ( qty * move.price_unit ) or 0.0
        # en caso de odc se actualiza el amount a un valor mas preciso
        if move.purchase_line_id:
            amount = float ( qty * move.purchase_line_id.price_unit )
        # si la unidad del movimiento es distinta a la referencial
        # se recalcula la cantidad en base a la referencial
        if uom_id != move.product_id.uom_id.id:
            factor_partial = float(move.product_uom.factor)
            factor_referen = float(move.product_id.uom_id.factor)
            proporcion = float(factor_partial/factor_referen)
            qty = proporcion > 0.0 and float(qty / proporcion) or qty
            # unidad referencial
            uom_id = move.product_id.uom_id.id
        if pick_type == 'in': # Compras
            if move.picking_id.purchase_id.id: # Compra
                shop_id = self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',move.picking_id.purchase_id.warehouse_id.id)])
            else: # Devoluciones
                shop_id = [move.picking_id.sale_id.shop_id.id]
            # se adicionan [qty, amount] en base al costo de compra
            shop_id and self._update_average_cost(cr, uid, qty, amount, product_id, shop_id[0])
        elif pick_type == 'out': # Ventas
            shop_id = move.picking_id.sale_id.shop_id.id
            substract = True
            use_avg_cost = True
            # se sustraen [qty, amount] de la sucursal donde se efectuo 
            # la venta y se hace en base a su costo promedio
            shop_id and self._update_average_cost(cr, uid, qty, amount, product_id, shop_id, substract, use_avg_cost)
        elif pick_type=='internal': # transferencias
            shop_id = move.location_id.usage == 'internal' and \
                    self._get_shop_by_location(cr, uid, move.location_id.id) or False
            shop_id = shop_id and shop_id[0]
            shop_dest_id = move.location_dest_id.usage == 'internal' and \
                    self._get_shop_by_location(cr, uid, move.location_dest_id.id) or False
            shop_dest_id = shop_dest_id and shop_dest_id[0]
            # se actualiza avg_cost si es entre dos sucursales
            if shop_id and shop_dest_id and shop_id != shop_dest_id:
                substract = True
                use_avg_cost = True
                # se sustraen [qty, amount] de la sucursal de origen en 
                # base a su costo promedio
                self._update_average_cost(cr, uid, qty, amount, product_id, shop_id, substract, use_avg_cost)
                # capturamos el costo promedio del origen y actualizamos amount
                amount = float (qty * self._get_average_cost(cr, uid, product_id, shop_id))
                # se adicionan [qty, amount] en la sucursal destino en 
                # base al costo promedio del origen (use_avg_cost = False)
                self._update_average_cost(cr, uid, qty, amount, product_id, shop_dest_id)
        elif active_model == 'stock.inventory.line': # movimiento de desecho
            loc_scrap_id = self.pool.get('stock.location').search(
                cr, uid, [('usage', '=', 'inventory'),('scrap_location','=',True)], context=context)
            loc_scrap_id = loc_scrap_id and loc_scrap_id[0]
            location_id = move.location_id.id
            location_dest_id = move.location_dest_id.id
            use_avg_cost = True
            if loc_scrap_id == location_dest_id:
                shop_id = move.location_id.usage == 'internal' and \
                        self._get_shop_by_location(cr, uid, location_id) or False
                shop_id = shop_id and shop_id[0]
                substract = True
                self._update_average_cost(cr, uid, qty, amount, product_id, shop_id, substract, use_avg_cost)
        else: # ajustes de inventario
            # capturamos la ubicacion de ajuste de invetario
            loc_inv_id = self.pool.get('stock.location').search(
                cr, uid, [('usage', '=', 'inventory'),('scrap_location','=',False)], context=context)
            loc_inv_id = loc_inv_id and loc_inv_id[0]
            location_id = move.location_id.id
            location_dest_id = move.location_dest_id.id
            shop_id = False
            use_avg_cost = True
            # evaluamos si hay perdida de inventario
            if loc_inv_id == location_dest_id:
                shop_id = self._get_shop_by_location(cr, uid, location_id)
                shop_id = shop_id and shop_id[0]
                # done: se sustrae de la sucursal origen el valor del costo promedio 
                # cancel: se acumula del costo promedio en el origen
                # cancel: False, done: True
                substract = (move.state == 'done')
                # se sustraen [qty, amount] de la sucursal de origen en 
                # base a su costo promedio (use_avg_cost = True)
                self._update_average_cost(cr, uid, qty, amount, product_id, shop_id, substract, use_avg_cost)
            # evaluamos si hay ganancia de inventario
            elif loc_inv_id == location_id:
                shop_id = self._get_shop_by_location(cr, uid, location_dest_id)
                shop_id = shop_id and shop_id[0]
                # done: se acumula del costo promedio en el destino
                # cancel: se sustrae de la sucursal destino el valor del costo promedio 
                # cancel: True, done: False
                substract = (move.state == 'cancel') 
                # se adicionan [qty, amount] en la sucursal destino en 
                # base a su costo promedio (use_avg_cost = True)
                self._update_average_cost(cr, uid, qty, amount, product_id, shop_id, substract, use_avg_cost)
        return {}
        
    _columns = {
        'shop_id' : fields.many2one('sale.shop', 'Sucursal', required=True ),
        'product_id' : fields.many2one('product.product', 'Producto', required=True ),
        'amount': fields.float('Monto Bs.', digits_compute=dp.get_precision('Average Cost'), required=True),
        #~ 'amount': fields.function(_amount_residual, digits_compute=dp.get_precision('Average Cost'), string='Monto Bs.',  type='float',
            #~ store={
                #~ 'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','move_id'], 50),
                #~ 'account.invoice.tax': (_get_invoice_tax, None, 50),
                #~ 'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
                #~ 'account.move.line': (_get_invoice_from_line, None, 50),
                #~ 'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
            #~ },
            #~ help="Remaining amount due."),
        'quantity': fields.float('Cantidad',  digits_compute=dp.get_precision('Average Cost Qty'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unidad de medida', required=True ),
        'cost': fields.function(_get_cost, type='float', string='Costo Promedio'),
        'last_cost': fields.float('Costo Anterior', digits_compute=dp.get_precision('Last Average Cost'), required=True),
    }

average_cost()
