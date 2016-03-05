#-*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 OpenERP Venezuela (http://openerp.com.ve)
# All Rights Reserved.
# Programmed by: Jose Suniaga <jose.suniaga@herrera.com.ve>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
from openerp import pooler
from openerp.osv import osv, fields
from openerp.tools.translate import _
#~ import openerp.addons.decimal_precision as dp
import time
import datetime

class pricelist_supplier(osv.Model):
    """
    Asistente para actualizar los precios de los
    productos a partir de una lista de precios 
    suministrada por el proveedor
    """
       
    _name="pricelist.supplier"

    def _get_qty(self,cr,uid,ids,field,arg,context=None):
        brw = self.browse(cr, uid, ids)
        res = {}
        for b in brw:
            c = 0
            for p in b.product_lines:
                c = c + 1
            res[b.id] = c
        return res
        
    def update_prices(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        partnerinfo_obj = self.pool.get('pricelist.partnerinfo')
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')
        item_obj = self.pool.get('product.pricelist.item')
        for brw in self.browse(cr, uid, ids,context):
            supplier_id = brw.supplier_id.id
            pricelist_id = brw.pricelist_id.id
            pricelist_type = pricelist_obj.browse(cr, uid, pricelist_id, context).type 
            base_pricelist_id = brw.base_pricelist_id.id
            this_date = context.get('date',False) or time.strftime('%Y-%m-%d')
            pricelist_version_ids = []
            # verificamos la version activa de la tarifa.
            if pricelist_id:
                pricelist_version_ids = version_obj.search(cr, uid, [
                                                            ('pricelist_id', '=', pricelist_id),
                                                            '|',
                                                            ('date_start', '=', False),
                                                            ('date_start', '<=', this_date),
                                                            '|',
                                                            ('date_end', '=', False),
                                                            ('date_end', '>=', this_date),
                                                        ])
            for line in brw.product_lines:
                # price_discount se usa para definir el descuento en caso de 
                # que la tarifa sea de compra y en caso de tarifa de venta
                # define el margen de ganancia
                price_discount = line.discount > 0 and ( line.discount * -1 / 100 ) or 0
                # si existe base_pricelist_id entonces pricelist_id es una 
                # tarifa de venta caso contrario seria tarifa de compra
                if base_pricelist_id: 
                    price_discount = line.margin > 0 and ( line.margin / 100 ) or 0
                # Por sugerencia se recomendo inicializar los precios de 
                # ventas de los productos con el mismo valor del costo.
                # Se comento la siguiente linea en caso que se requiera 
                # devolver esta sugerencia, es decir, precio != costo
                # product_obj.write(cr,uid,line.product_id.id,{'standard_price':line.standard_price,'list_price':line.price})
                product_obj.write(cr,uid,line.product_id.id,{'standard_price':line.standard_price,'list_price':line.standard_price})
                if pricelist_version_ids:
                    item_ids = item_obj.search(cr, uid, [('price_version_id','=',pricelist_version_ids[0]),('product_id','=',line.product_id.id)],context=context)
                    if item_ids:
                        item_obj.write(cr,uid,item_ids[0],{ 'base': base_pricelist_id and -1 or 2,
                                                            'base_pricelist_id': base_pricelist_id,
                                                            'price_discount': price_discount
                                                          },context=context)
                    else:
                        item_obj.create(cr,uid,{'min_quantity':0.00,
                                                'price_discount': price_discount,
                                                'name':line.product_id.code,
                                                'product_id':line.product_id.id,
                                                'base': base_pricelist_id and -1 or 2,
                                                'base_pricelist_id': base_pricelist_id,
                                                'price_version_id':pricelist_version_ids[0],
                                                'sequence':1,
                                                'price_round':0.00,
                                                'price_min_margin':0.00,
                                                'price_max_margin':0.00,
                                                'price_surcharge':0.00,
                                               })
                supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('name','=',supplier_id),('product_id','=',line.product_id.id)],context=context)
                if supplierinfo_ids and base_pricelist_id:
                    supplierinfo_obj.write(cr,uid,supplierinfo_ids[0],{'product_code':line.code})
                    supplierinfo_brw = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0],context)
                    partnerinfo_ids = supplierinfo_brw.pricelist_ids
                    if partnerinfo_ids:
                        partnerinfo_id = partnerinfo_obj.search(cr, uid, [('min_quantity','in',[1.00]),('suppinfo_id','=',supplierinfo_brw.id)],context=context)
                        partnerinfo_id and partnerinfo_obj.write(cr,uid,partnerinfo_id[0],{'price':line.cost}) or \
                        partnerinfo_obj.create(cr,uid,{'min_quantity':1.00,'price':line.cost,'suppinfo_id':supplierinfo_brw.id})
                    else:
                        partnerinfo_obj.create(cr,uid,{'min_quantity':1.00,'price':line.cost,'suppinfo_id':supplierinfo_brw.id})
            self.write(cr, uid, brw.id, {'draft':False, 'undraft_date':this_date},context)
        return {}
        
    def cancel_update(self, cr, uid, ids, context=None):
        for brw in self.browse(cr, uid, ids,context):
            self.write(cr, uid, brw.id, {'draft':False},context)
        return {}
        
    _columns = {
        'name': fields.char('name', size=256, required=True),
        'product_lines': fields.one2many('pricelist.supplier.line', 'price_supplier_id', 'Productos'),
        'supplier_id': fields.many2one('res.partner', string='Proveedor', required=True),
        'pricelist_id': fields.many2one('product.pricelist', string='Tarifa', required=True, help="Tarifa por defecto para este proveedor"),
        'base_pricelist_id': fields.many2one('product.pricelist', string='Tarifa base', help="Tarifa base para capturar los costos del proveedor"),
        'draft': fields.boolean('Borrador'),
        'product_qty': fields.function(_get_qty, type='integer', string='Cantidad de productos'),
        'undraft_date': fields.date('Fecha de aplicacion', help="Fecha cuando se proceso la actualización de la tarifa"),
        #~ 'date_begin': fields.date('Fecha inicial', required=True, help="Fecha inicial de validez para esta tarifa"),
        #~ 'date_end': fields.date('Fecha final', help="Fecha de fin de validez de esta tarifa. Deje en blanco si es indefinida"),
    }
    
    _defaults = {
        'draft': True,
    }


class pricelist_supplier_line(osv.Model):
    
    _name="pricelist.supplier.line"
    
    _columns = {
        'product_id': fields.many2one('product.product', string='Producto', required=True, help="Producto del proveedor que se desea actualizar costo/precio"),
        'code': fields.char('Código Prov.', help="Código de Producto del Proveedor. Este código es el que indentifica al producto en el presupuesto del proveedor"),
        'price': fields.float('Precio Unidad', required=True, help="Precio unitario de venta. Precio base para calcular el precio al cliente"),
        'standard_price': fields.float('Precio Total', required=True, help="Precio costo de venta. Indica el costo de compra del producto segun su unidad de venta."),
        'net_price': fields.float('Precio Total', required=True, help="Precio costo de venta. Indica el costo de compra del producto segun su unidad de venta."),
        'cost': fields.float('Costo', required=True, help="Precio de costo bruto. Precio base que indica el costo con que se le compra el producto al proveedor"),
        'net_cost': fields.float('Costo neto', required=True, help="Precio de costo neto. Precio base que indica el costo con que se le compra el producto al proveedor menos el descuento"),
        'margin': fields.float('Margen (%)', required=True, help="Margen de ganancia. Margen de rentabilidad que se espera obtener de las ventas del producto"),
        'price_supplier_id': fields.many2one('pricelist.supplier', string='Proveedor', required=True, ondelete='cascade'),
        'discount': fields.float('Descuento', required=True, help="Porcentaje de descuento. Indica el descuento lineal a este producto. En caso de no haber descuento dejar en cero (0)"),
    }
