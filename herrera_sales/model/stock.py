# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class _inherited_stock_location(osv.Model):
    _inherit = 'stock.location'

    def get_parent(self, cr, uid, ids, location_id, context = None):
        parent = self.browse(cr, uid, location_id).location_id.id
        if not self.pool.get('stock.warehouse').search(cr, uid, [('lot_stock_id','=',parent)]):
            parent = self.get_parent(cr, uid, ids, parent, context)
        return parent

    def get_stock_location(self, cr, uid, ids, product_id, product_qty, context = None):
        uom_obj = self.pool.get('product.uom')
        uom_rounding = self.pool.get('product.product').browse(cr, uid, product_id, context=context).uom_id.rounding
        result = []
        amount = 0.0
        #buscamos el id del padre raiz del location_id
        parent = False
        location_id = ids[0]
        if not self.pool.get('stock.warehouse').search(cr, uid, [('lot_stock_id','=',location_id)]):
            parent = self.get_parent(cr, uid, ids, location_id, context)
        else:
            if not self.pool.get('stock.location').search(cr, uid, [('chained_location_id','=', location_id)]):
                parent = location_id
                
        # verificando si poseen numeros de lote y obtenemos el criterio de orden (fecha de vencimiento o pvm)
        location_ids = []
        cr.execute(""" SELECT move.location_dest_id FROM stock_move AS move
                            LEFT JOIN stock_production_lot AS lot ON lot.id = move.prodlot_id
                            JOIN stock_location as loca ON loca.id = move.location_dest_id
                            WHERE move.product_id = %s
                            AND move.state = 'done'
                            AND loca.usage = 'internal'
                            AND loca.chained_location_type <> 'customer'
                            AND loca.internal_type = 'hall'
                            AND move.location_dest_id <> %s
                            ORDER BY lot.use_date, lot.pvm ASC"""%(product_id, parent))
        resul = cr.dictfetchall()
        location_ids = resul and \
           map(lambda x: x['location_dest_id'], resul) or \
           self.search(cr, uid, [('location_id', 'child_of', parent)])
            
        for i in location_ids:
            childs = self.search(cr, uid, [('location_id', 'child_of', i)])
            #~ print '¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨childs',childs
            if len(childs) == 1: # ubicaciones de nivel mas bajo
                #consulta para obtener la cantidad virtual existente de ese producto en el almacen
                cr.execute("""SELECT product_uom, prodlot_id, sum(product_qty) AS product_qty
                          FROM stock_move
                          WHERE location_dest_id=%s AND
                                location_id<>%s AND
                                product_id=%s AND
                                state='done'
                          GROUP BY product_uom, prodlot_id
                       """,
                       (childs[0], childs[0], product_id))
                results = cr.dictfetchall()

                #consulta para obtener lo que se vendera
                cr.execute("""SELECT product_uom, prodlot_id, -sum(product_qty) AS product_qty
                              FROM stock_move
                              WHERE location_id=%s AND
                                    location_dest_id<>%s AND
                                    product_id=%s AND
                                    state in ('done', 'assigned')
                              GROUP BY product_uom, prodlot_id
                           """,(childs[0], childs[0], product_id))
                results += cr.dictfetchall()
                #~ print 'hijos %s, iteracion : %s'%(i, childs)
                total = 0.0
                results2 = 0.0
                for r in results:
                    amount = uom_obj._compute_qty(cr, uid, r['product_uom'], r['product_qty'], context.get('uom', False))
                    results2 += amount
                    total += amount
                if total <= 0.0:
                    continue
                amount = results2
                compare_qty = float_compare(amount, 0, precision_rounding=uom_rounding)
                if compare_qty == 1:
                    if amount > min(total, product_qty):
                        amount = min(product_qty, total)
                    result.append((amount, i, r['prodlot_id']))
                    product_qty -= amount
                    total -= amount
                    if product_qty <= 0.0:
                        return result
                    if total <= 0.0:
                        continue
        return result

    def _product_reserve(self, cr, uid, ids, product_id, product_qty, context=None, lock=False):
        res = {}
        this = self.browse(cr, uid, ids[0],  context=context)
        # Ubicaciones de Distribucion: son las que se tomaran en 
        # cuenta para el Analisis de Disponibilidad
        # << Por ahora sólo pasillos >>
        if this.internal_type in ['picking','in','reinstatement','procurement','alternate','output']:
            res = super(_inherited_stock_location,self)._product_reserve(cr, uid, ids, 
                    product_id, product_qty, context, lock)
        else:
            res = self.get_stock_location(cr, uid, ids, product_id, product_qty, context)
        return res

_inherited_stock_location()
