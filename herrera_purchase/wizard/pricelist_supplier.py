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

class pricelist_supplier(osv.osv_memory):
    """
    Asistente para actualizar los precios de los
    productos a partir de una lista de precios 
    suministrada por el proveedor
    """

    _name="pricelist.supplier.wizard"

    def _get_product_lines(self, cr, uid, context=None):
        if context is None:
            context = {}
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        partnerinfo_obj = self.pool.get('pricelist.partnerinfo')
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist_item_obj = self.pool.get('product.pricelist.item')
        product_obj = self.pool.get('product.product')
        pricelist_id = context.get('pricelist_id', False)
        pricelist_base = context.get('pricelist_base', False)
        pricelist_type = context.get('pricelist_type', False)
        supplier_id = context.get('active_id', False)
        res = []
        if supplier_id:
            # capturamos la cartera de productos del proveedor
            supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('name','=',supplier_id)],context=context)
            # validamos si hay algun criterio de ordenamiento
            if context.get('order_by', False):
                product_dict = {}
                product_sort = []
                for supplierinfo_brw in supplierinfo_obj.browse(cr, uid, supplierinfo_ids, context):
                    product_brw = product_obj.browse(cr, uid, supplierinfo_brw.product_id.id, context)
                    # validamos que el producto este activo
                    if product_brw.active:
                        product_dict[product_brw.id] = eval('product_brw.%s'%context['order_by'])
                        # reordenamos los productos
                        product_sort = sorted(product_dict.items(), key=lambda x: x[1])
                if product_sort:
                    # limpiamos la cartera de productos
                    supplierinfo_ids = []
                    # almacenamos nuevamente la cartera de productos ya ordenada
                    for p in product_sort:
                        supplierinfo_id = supplierinfo_obj.search(cr, uid, [('name','=',supplier_id),('product_id','=',p[0])],context=context)
                        supplierinfo_id and supplierinfo_ids.append(supplierinfo_id[0])
            for supplierinfo_brw in supplierinfo_obj.browse(cr, uid, supplierinfo_ids, context):
                margin = 0.0
                discount = 0.0
                factor_po = 1.00
                factor_so = 1.00
                #costo bruto (segun UdV o referencia)
                standard_price = supplierinfo_brw.product_id.standard_price 
                #precio de venta
                price = supplierinfo_brw.product_id.list_price
                price_dict = pricelist_obj.price_get(cr, uid, [pricelist_id],
                    supplierinfo_brw.product_id.id, 1.0, supplier_id, {
                    'uom': supplierinfo_brw.product_id.uom_id.id,
                    })
                item_id = price_dict['item_id'][pricelist_id]
                # descuento que tiene la lista de precio (pricelist_id)
                item_brw = pricelist_item_obj.browse(cr, uid, item_id, context)
                if hasattr(item_brw,'price_discount'):
                    discount = abs(item_brw.price_discount) * 100
                # costo neto (segun UdV o referencia)
                net_price = standard_price * ( 1 - discount / 100 )
                # si se va a actualizar una tarifa de venta, deben calcularse
                # los costo a partir de una tarifa base (pricelist_base)
                if pricelist_type == 'sale':
                    # el campo price_discount se guarda el margen en casos de 
                    # tarifas de venta y para tarifas de compra el descuento
                    margin = discount
                    price = standard_price / ( 1 - margin / 100 )
                # cost bruto (segun UdC)
                cost = standard_price
                # costo neto (segun UdC)
                net_cost = net_price
                if supplierinfo_brw.product_id.uom_id.id != supplierinfo_brw.product_id.uom_po_id.id:
                    factor_po = float(supplierinfo_brw.product_id.uom_po_id.factor)
                    factor_so = float(supplierinfo_brw.product_id.uom_id.factor)
                    proporcion = float(factor_po/factor_so)
                    cost = cost / proporcion
                    net_cost = net_cost / proporcion
                res.append((0,0,{
                        'supplier_id':supplier_id,
                        'code':supplierinfo_brw.product_code,
                        'product_id':supplierinfo_brw.product_id.id,
                        #~ 'name':supplierinfo_brw.product_id.name,
                        #~ 'default_code':supplierinfo_brw.product_id.default_code,
                        'discount': discount,
                        'cost': cost,
                        'net_cost': net_cost,
                        'margin': margin,
                        'price': price,
                        'standard_price': standard_price,
                        'net_price': net_price,
                        }))
        return res
        
    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        #Esta función por defecto devuelve un diccionario, con los valores que se cargan por defecto
        res = super(pricelist_supplier, self).default_get(cr, uid, fields_list, context)
        if 'product_lines' in context:
            res.update({'product_lines': context['product_lines']})
        if 'discount' in context:
            res.update({'discount': context['discount']})
        if 'unique_discount' in context:
            res.update({'unique_discount': context['unique_discount']})
        if 'margin' in context:
            res.update({'margin': context['margin']})
        if 'unique_margin' in context:
            res.update({'unique_margin': context['unique_margin']})
        if 'update_later' in context:
            res.update({'update_later': context['update_later']})
        if 'wizard_ref' in context:
            res.update({'name': context['wizard_ref']})
        return res
        
    _columns = {
        'name': fields.char('name', size=256),
        'product_lines': fields.one2many('pricelist.supplier.line.wizard', 'wzr_id', 'Productos'),
        'supplier_id': fields.integer('Proveedor'),
        'pricelist_id': fields.integer('Tarifa'),
        #~ 'pricelist_id': fields.many2one('product.pricelist', string='Tarifa', required=True, help="Tarifa por defecto para este proveedor"),
        #~ 'category_id': fields.many2one('product.category', string='Categoría de producto', required=True, help="Establecer una categoria de producto si esta tarifa solo se aplicará a los productos de una categoria y sus hijos. Dejar vacio para aplicar a todos los productos, inclusive los que no son de este proveedor."),
        #~ 'update_pricelist': fields.boolean('Tarifa', help="Actualizar Tarifa"),
        'update_later': fields.boolean('Actualizar despues', help="Actualizar despues"),
        'unique_discount': fields.boolean('Descuento unico', help="Aplicar el mismo descuento a todas las lineas"),
        'unique_margin': fields.boolean('Definir margen unico', help="Aplicar el mismo margen de ganancia a todas las lineas"),
        #~ 'new_pricelist': fields.boolean('Tarifa', help="Nueva Tarifa"),
        #~ 'name': fields.char('Nombre', size=64),
        #~ 'date_begin': fields.date('Fecha inicial', required=True, help="Fecha inicial de validez para esta tarifa"),
        #~ 'date_end': fields.date('Fecha final', help="Fecha de fin de validez de esta tarifa. Deje en blanco si es indefinida"),
        'discount': fields.float('Descuento (%)', help="Monto de descuento para aplicar a todas las lineas"),  
        'margin': fields.float('Margin (%)', help="Monto porcentual de margen de ganancia para aplicar a todas las lineas"),  
        #~ 'pricelist_type': fields.char('Tipo de tarifa', size=8, help="Si es tarifa de compra o de venta")
        }
    
    def update_prices(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wzr = ids and self.browse(cr, uid, ids, context=context)[0]
        supplier_id = wzr and wzr.supplier_id
        pricelist_id = wzr and wzr.pricelist_id
        #~ update_pricelist = wzr and wzr.update_pricelist
        update_later = wzr and wzr.update_later
        product_lines = wzr and wzr.product_lines
        product_obj = self.pool.get('product.product')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        partnerinfo_obj = self.pool.get('pricelist.partnerinfo')
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')
        item_obj = self.pool.get('product.pricelist.item')
        this_date = context.get('date') or time.strftime('%Y-%m-%d')
        pricelist_base = context.get('pricelist_base', False)
        #~ start_date = wzr and wzr.date_begin or time.strftime('%Y-%m-%d')
        #~ end_date = wzr and wzr.date_end
        pricelist_ids = context.get('pricelist_type', False) and pricelist_obj.search(cr, uid, [('type','=',context['pricelist_type'])])
        pricelist_version_ids = []
        lines = []
        product = []
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
        for line in product_lines:
            if not update_later:
                product.append({'product_id':line.product_id.id, 'cost':line.cost, 'price':line.price})
                supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('name','=',supplier_id),('product_id','=',line.product_id.id)],context=context)
                if pricelist_version_ids:
                    # price_discount se usa para definir el descuento en caso de 
                    # que la tarifa sea de compra y en caso de tarifa de venta
                    # define el margen de ganancia
                    price_discount = line.discount > 0 and ( line.discount * -1 / 100 ) or 0
                    # si existe pricelist_base entonces pricelist_id es una 
                    # tarifa de venta caso contrario seria tarifa de compra
                    if pricelist_base: 
                        price_discount = line.margin > 0 and ( line.margin / 100 ) or 0
                    item_ids = item_obj.search(cr, uid, [('price_version_id','=',pricelist_version_ids[0]),('product_id','=',line.product_id.id)],context=context)
                    if item_ids:
                        item_obj.write(cr,uid,item_ids[0],{'price_discount': price_discount },context=context)
                    else:
                        item_obj.create(cr,uid,{'min_quantity':0.00,
                                                'price_discount': price_discount,
                                                'name':line.product_id.code,
                                                'product_id':line.product_id.id,
                                                'base': pricelist_base and -1 or 2,
                                                'base_pricelist_id': pricelist_base,
                                                'price_version_id':pricelist_version_ids[0],
                                                'sequence':1,
                                                'price_round':0.00,
                                                'price_min_margin':0.00,
                                                'price_max_margin':0.00,
                                                'price_surcharge':0.00,
                                               })
                # se hace este proceso solo para tarifas de compra
                if supplierinfo_ids and not pricelist_base:
                    supplierinfo_obj.write(cr,uid,supplierinfo_ids[0],{'product_code':line.code})
                    supplierinfo_brw = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0],context)
                    partnerinfo_ids = supplierinfo_brw.pricelist_ids
                    if partnerinfo_ids:
                        partnerinfo_id = partnerinfo_obj.search(cr, uid, [('min_quantity','in',[1.00]),('suppinfo_id','=',supplierinfo_brw.id)],context=context)
                        partnerinfo_id and partnerinfo_obj.write(cr,uid,partnerinfo_id[0],{'price':line.cost}) or \
                        partnerinfo_obj.create(cr,uid,{'min_quantity':1.00,'price':line.cost,'suppinfo_id':supplierinfo_brw.id})
                    else:
                        partnerinfo_obj.create(cr,uid,{'min_quantity':1.00,'price':line.cost,'suppinfo_id':supplierinfo_brw.id})
            else:
                lines.append((0,0,{
                        'code':line.code,
                        'product_id':line.product_id.id,
                        'discount': not pricelist_base and line.discount or 0.0,
                        'margin': pricelist_base and line.margin or 0.0,
                        'cost': line.cost,
                        'standard_price': line.standard_price,
                        'net_cost': not pricelist_base and line.net_cost or 0.0,
                        'net_price': not pricelist_base and line.net_price or 0.0,
                        'price': pricelist_base and line.price or 0.0,
                        }))
        
        # Actualizamos los costos y precios de las fichas de productos
        for d in product:
            product_brw = product_obj.browse(cr, uid, d['product_id'] ,context)
            # Llamamos al campo funcional para que se actualice el historico
            product_brw.cost_historical
            product_brw.list_price_historical
            proporcion = 1.00
            if product_brw.uom_id.id != product_brw.uom_po_id.id:
                factor_po = float(product_brw.uom_po_id.factor)
                factor_so = float(product_brw.uom_id.factor)
                proporcion = float(factor_po/factor_so)
            standard_price = d['cost'] * proporcion
            # Por sugerencia se recomendo inicializar los precios de 
            # ventas de los productos con el mismo valor del costo.
            # Se comento la siguiente linea en caso que se requiera 
            # devolver esta sugerencia, es decir, precio != costo
            # product_obj.write(cr,uid,line.product_id.id,{'standard_price':standard_price,'list_price':d['price']})
            product_brw.write({'standard_price':standard_price,'list_price':standard_price})
        
        # Guardamos en el modelo pricelist.supplier para que sea actualizado luego
        if lines:
            name = wzr and wzr.name
            self.pool.get('pricelist.supplier').create(cr,uid,{
                                                'name': name,
                                                'product_lines': lines,
                                                'supplier_id': supplier_id,
                                                'pricelist_id': pricelist_id,
                                                'base_pricelist_id': pricelist_base,
                                                #~ 'draft': True,
                                                })
        return {}
    
    def update_discount(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wzr = ids and self.browse(cr, uid, ids, context=context)[0]
        update_later = wzr and wzr.update_later or False
        product_lines = wzr and wzr.product_lines
        discount_unq = wzr and wzr.discount
        wizard_ref = wzr and wzr.name
        lines = []
        for line in product_lines:
            discount = line.standard_price > 0.0 and discount_unq or 0.0
            proporcion = line.cost > 0.0 and line.standard_price / line.cost or 1
            net_price = line.standard_price * ( 1 - discount / 100 )
            net_cost = net_price / proporcion
            lines.append((0,0,{
                        'code':line.code,
                        'product_id':line.product_id.id,
                        'discount': discount,
                        'cost': line.cost,
                        'net_cost': net_cost,
                        'standard_price': line.standard_price,
                        'net_price': net_price,
                        }))
        if lines:
            # se almacena en context para que al recargar el wizard
            # el metodo default_get despliegue los valores
            context['product_lines'] = lines
            context['discount'] = discount
            context['unique_discount'] = True
            context['update_later'] = update_later
            context['wizard_ref'] = wizard_ref
        # se captura el resource_id de la vista para recargar el wizard
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','pricelist_supplier_wizard')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pricelist.supplier.wizard',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
    def update_margin(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wzr = ids and self.browse(cr, uid, ids, context=context)[0]
        update_later = wzr and wzr.update_later or False
        product_lines = wzr and wzr.product_lines
        margin_unq = wzr and wzr.margin
        wizard_ref = wzr and wzr.name
        lines = []
        for line in product_lines:
            margin = line.standard_price > 0.0 and margin_unq or 0.0
            price = line.standard_price * ( 1 + margin / 100 )
            lines.append((0,0,{
                        'code':line.code,
                        'product_id':line.product_id.id,
                        'cost': line.cost,
                        'standard_price': line.standard_price,
                        'margin': margin,
                        'price': price,
                        }))
        if lines:
            # se almacena en context para que al recargar el wizard
            # el metodo default_get despliegue los valores
            context['product_lines'] = lines
            context['margin'] = margin
            context['unique_margin'] = True
            context['update_later'] = update_later
            context['wizard_ref'] = wizard_ref
        # se captura el resource_id de la vista para recargar el wizard
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','pricelist_supplier_wizard')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pricelist.supplier.wizard',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
    _defaults = {
        'product_lines': _get_product_lines,
        'supplier_id' :  lambda self,cr,uid,context:context.get('active_id',False),
        'pricelist_id':  lambda self,cr,uid,context:context.get('pricelist_id',False),
    }

pricelist_supplier()

class pricelist_supplier_line(osv.osv_memory):
    
    _name="pricelist.supplier.line.wizard"
    
    def _get_standard_price(self,cr,uid,ids,field,arg,context=None):

        brw = self.browse(cr, uid, ids)
        res = {}
        for b in brw:
            res[b.id] = 0.0
        return res
        
    def onchange_cost(self, cr, uid, ids, product_id, cost=False, margin=False, discount=False, context=None):
        res = {}
        if not margin:
            margin = 0.00
        if cost:
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr, uid, product_id,context)
            proporcion = 1.00
            if product_brw.uom_id.id != product_brw.uom_po_id.id:
                factor_po = float(product_brw.uom_po_id.factor)
                factor_so = float(product_brw.uom_id.factor)
                proporcion = float(factor_po/factor_so)
            standard_price = cost * proporcion
            price = standard_price * ( 1 + float(margin) / 100.00 )
            res = { 'value': {'price': price, 'standard_price': standard_price} }
            if isinstance(discount, (int, float)):
                discount = float(discount)
                net_cost = cost * ( 1 - float(discount) / 100.00 )
                net_price = standard_price * ( 1 - float(discount) / 100.00 )
                res['value'].update({'net_cost': net_cost, 'net_price': net_price})
        return res
        
    def onchange_discount(self, cr, uid, ids, cost=False, standard_price=False, discount=False, context=None):
        res = {}
        if cost and standard_price and discount:
            discount = float(discount)
            net_cost = cost * ( 1 - float(discount) / 100.00 )
            net_price = standard_price * ( 1 - float(discount) / 100.00 )
            res = { 'value': {'net_cost': net_cost, 'net_price': net_price} }
        return res
    
    def onchange_margin(self, cr, uid, ids, product_id, cost=False, margin=False, context=None):
        res = {}
        if cost and margin:
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr, uid, product_id,context)
            proporcion = 1.00
            if product_brw.uom_id.id != product_brw.uom_po_id.id:
                factor_po = float(product_brw.uom_po_id.factor)
                factor_so = float(product_brw.uom_id.factor)
                proporcion = float(factor_po/factor_so)
            price = cost * proporcion / ( 1.0 - float(margin) / 100.00 )
            res = { 'value': {'price': price } }
        
        return res
    
    _columns = {
        'product_id': fields.many2one('product.product', string='Producto', required=True, help="Producto del proveedor que se desea actualizar costo/precio"),
        'code': fields.char('Código Prov.', help="Código de Producto del Proveedor. Este código es el que indentifica al producto en el presupuesto del proveedor"),
        'price': fields.float('Precio Unidad', help="Precio unitario de venta. Precio base para calcular el precio al cliente"),
        'standard_price': fields.float('Precio Total', required=True, help="Precio costo de venta. Indica el costo de compra del producto segun su unidad de venta."),
        'net_price': fields.float('Precio Total', help="Precio costo de venta. Indica el costo de compra del producto segun su unidad de venta."),
        #~ 'standard_price': fields.function(_get_standard_price,
                                         #~ method=True, string='Latest Price',
                                         #~ type='float',
                                         #~ digits_compute=dp.get_precision(
                                             #~ 'standard_price'),
                                         #~ store={'product.product': ( lambda
                                             #~ self, cr, uid, ids, c={}: ids, [
                                                 #~ 'list_price'], 50), },
                                             #~ help="""Precio total de venta. Precio de venta del producto segun su unidad de compra."""),
        'cost': fields.float('Costo', required=True, help="Precio de costo bruto. Precio base que indica el costo con que se le compra el producto al proveedor"),
        'net_cost': fields.float('Costo neto', help="Precio de costo neto. Precio base que indica el costo con que se le compra el producto al proveedor menos el descuento"),
        'margin': fields.float('Margen (%)', help="Margen de ganancia. Margen de rentabilidad que se espera obtener de las ventas del producto"),
        'wzr_id': fields.many2one('pricelist.supplier.wizard', string='Proveedor', required=True),
        'discount': fields.float('Descuento', help="Porcentaje de descuento. Indica el descuento lineal a este producto. En caso de no haber descuento dejar en cero (0)"),
        #~ 'apply_discount': fields.boolean('Descuento', help="Marque si desea aplicar descuento a este producto"),
        #~ 'name': fields.related('product_id', 'name', type='char', relation='product.product', string='Name'),
        #~ 'default_code': fields.related('product_id', 'default_code', type='char', relation='product.product', string='Code'),
    }
    
    _defaults = {
        #~ 'supplier_id' :  lambda self,cr,uid,context:context.get('active_id',[False]),
    }
    
pricelist_supplier_line()


class pricelist_selector(osv.osv_memory):
    """
    Asistente para actualizar los precios de los
    productos a partir de una lista de precios 
    suministrada por el proveedor
    """
       
    _name="pricelist.selector.wizard"
    
    def onchange_pricelist_type(self, cr, uid, ids, pricelist_type, context=None):
        if context is None:
            context = {}
        res = {'value': {'pricelist_id': False, 'pricelist_base': False} }
        if 'active_id' in context:
            brw = self.pool.get('res.partner').browse(cr, uid, context['active_id'], context=context)
            if pricelist_type == 'sale':
                res['value'].update({ 'pricelist_id' : brw.property_product_pricelist.id })
            else:
                res['value'].update({ 'pricelist_id' : brw.property_product_pricelist_purchase.id })
        return res
    
    
    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', string='Tarifa a actualizar', required=True, help="Tarifa que desea actualizar"),
        'pricelist_base': fields.many2one('product.pricelist', string='Basada en', help="Tarifa de donde se toma el precio coste base"),
        'pricelist_type': fields.selection([
            ('purchase', 'Tarifa de compra'),
            ('sale', 'Tarifa de venta'),
        ], 'Tipo de tarifa', help="Indica si deseamos actualizar una tarifa de compra o una tarifa de venta"),
        'order_by': fields.selection([
            ('categ_id.name', 'Categoria'),
            ('code', 'Codigo interno'),
            ('name', 'Nombre'),
        ], 'Ordenar los productos', help="Define ordenamiento de los productos"),
    }
    
    def action_next(self, cr, uid, ids, context=None):
        """
        Goes to Next page.
        """
        if context is None:
            context = {}
        if not context.get('active_id',False):
            raise osv.except_osv(_('Ha ocurrido un error!'),
                    _('Debe seleccionar un proveedor para poder continuar, para mas detalles consulte con el administrador del sistema'))
        wzr = ids and self.browse(cr, uid, ids, context=context)[0]
        context['pricelist_id'] = wzr and wzr.pricelist_id.id
        context['pricelist_type'] = wzr and wzr.pricelist_type
        context['order_by'] = wzr and wzr.order_by
        if context['pricelist_type'] == 'sale':
             context['pricelist_base'] = wzr and wzr.pricelist_base.id
        
        return {
            'name': 'Actualizar lista de productos',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'pricelist.supplier.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            #~ 'search_view_id': search_id[0],
            'context': context
        }
    
pricelist_selector()
