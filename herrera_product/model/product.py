# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

import decimal_precision as dp
import pooler
import time
import math

class inherited_product(osv.osv):
    
    '''Herencia del modelo product.product para agregar campos necesarios en Herrera C.A. '''
    
    _inherit = 'product.product'
    
    # replace original function for _get_historical_price (in vauxoo's product_historical_price module)
    def _get_historical_price(self, cr, uid, ids, field_name, field_value,
                             arg, context={}):
        res = {}
        #~ res = super(inherited_product,self)._get_historical_price(cr, uid, ids, field_name, field_value,
                             #~ arg, context={})
        product_hist = self.pool.get('product.historic.price')
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist_item_obj = self.pool.get('product.pricelist.item')
        pricelist_ids = pricelist_obj.search(cr, uid, [('type','=','sale')])
        for product_id in ids:
            product = self.browse(cr, uid, product_id)
            for pricelist_id in pricelist_ids:
                net_price = 0.0
                list_price = 0.0
                error_margin = 0.01
                create_hist = True
                try:
                    price_dict = pricelist_obj.price_get(cr, uid, [pricelist_id],
                        product_id, 1.0, None, {
                        'uom': product.uom_id.id,
                        })
                    item_id = price_dict['item_id'][pricelist_id]
                    # descuento que tiene la lista de precio (pricelist_id)
                    item_read = pricelist_item_obj.read(cr, uid, item_id, ['price_discount'], context=context)
                    margin = abs(item_read['price_discount']) * 100
                    # costo neto (segun UdV o referencia)
                    net_price = price_dict[pricelist_id]
                    list_price = net_price * ( 1 - margin / 100 )
                except:
                    pass
                if net_price:
                    product_hist_ids = product_hist.search(cr, uid, [('pricelist_id','=',pricelist_id),('product_id','=',product_id)])
                    product_hist_id = False
                    if product_hist_ids:
                        product_hist_id = max(product_hist_ids) # Extraemos la ultima actualizacion
                        create_hist = abs(net_price - product_hist.browse(cr, uid, product_hist_id).net_price) >= error_margin
                    if create_hist:
                        product_hist_id = product_hist.create(cr, uid, {
                            'product_id': product_id,
                            'pricelist_id': pricelist_id,
                            'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price': list_price,
                            'net_price': net_price,
                            'margin': margin,
                            'product_uom': product.uom_id.id,
                        }, context)
                    if product_hist_id:
                        # Ultimo precio
                        res[product_id] = product_hist.browse(cr, uid, product_hist_id).net_price

        return res
    
    # replace original function for _get_historical_cost (in vauxoo's product_historical_price module)
    def _get_historical_cost(self, cr, uid, ids, field_name, field_value,
                             arg, context={}):
        res = {}
        #~ res = super(inherited_product,self)._get_historical_cost(cr, uid, ids, field_name, field_value,
                             #~ arg, context={})
        product_hist = self.pool.get('product.historic.cost')
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist_item_obj = self.pool.get('product.pricelist.item')
        pricelist_ids = pricelist_obj.search(cr, uid, [('type','=','purchase')])
        for product_id in ids:
            product = self.browse(cr, uid, product_id)
            for pricelist_id in pricelist_ids:
                net_price = 0.0
                standard_price = 0.0
                error_margin = 0.01
                create_hist = True
                try:
                    price_dict = pricelist_obj.price_get(cr, uid, [pricelist_id],
                        product_id, 1.0, None, {
                        'uom': product.uom_po_id.id,
                        })
                    item_id = price_dict['item_id'][pricelist_id]
                    # descuento que tiene la lista de precio (pricelist_id)
                    item_read = pricelist_item_obj.read(cr, uid, item_id, ['price_discount'], context=context)
                    #~ if hasattr(item_brw,'price_discount'):
                    discount = abs(item_read['price_discount']) * 100
                    # costo neto (segun UdV o referencia)
                    net_price = price_dict[pricelist_id]
                    standard_price = net_price / ( 1 - discount / 100 )
                except:
                    pass
                if net_price:
                    product_hist_ids = product_hist.search(cr, uid, [('pricelist_id','=',pricelist_id),('product_id','=',product_id)])
                    product_hist_id = False
                    if product_hist_ids:
                        product_hist_id = max(product_hist_ids) # Extraemos la ultima actualizacion
                        create_hist = abs(net_price - product_hist.browse(cr, uid, product_hist_id).net_price) >= error_margin
                    if create_hist:
                        product_hist_id = product_hist.create(cr, uid, {
                            'product_id': product_id,
                            'pricelist_id': pricelist_id,
                            'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price': standard_price,
                            'net_price': net_price,
                            'discount': discount,
                            'product_uom': product.uom_po_id.id,
                        }, context)
                    if product_hist_id:
                        # Ultimo costo
                        res[product_id] = product_hist.browse(cr, uid, product_hist_id).net_price

        return res
    
    def update_historical(self, cr, uid, ids, context=None):
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist_item_obj = self.pool.get('product.pricelist.item')
        for product_id in ids:
            # Limpiamos el historial
            old_cost_ids = self.pool.get('product.historic.cost').search(cr, uid,[('product_id','=',product_id)])
            old_price_ids = self.pool.get('product.historic.price').search(cr, uid,[('product_id','=',product_id)])
            self.pool.get('product.historic.cost').unlink(cr, uid, old_cost_ids)
            self.pool.get('product.historic.price').unlink(cr, uid, old_price_ids)
            self.write(cr, uid, product_id, { 'historical_ok':True })
        return True
    
    _columns = {
             'ean14': fields.char('Codigo EAN14', size=14, help="International Article Number used for product identification."),
             'cod8': fields.char('Codigo EAN8', size=8, help="Codigo de 8 caracteres para identificar productos."),
             'sica_id':fields.many2one('product.sica', 'SICA', help='Indicates if this product applied SICA'),
             'list_price_historical': fields.function(_get_historical_price,
                                         method=True, string='Latest Price',
                                         type='float',
                                         digits_compute=dp.get_precision(
                                             'List_Price_Historical'),
                                         store={'product.product': ( lambda
                                             self, cr, uid, ids, c={}: ids, [
                                                 'list_price','standard_price','historical_ok'], 50), },
                                             help="""Latest Recorded Historical
                                             Value"""),
             'cost_historical': fields.function(_get_historical_cost, method=True,
                                   string=' Latest Cost', type='float',
                                   digits_compute=dp.get_precision(
                                       'Cost_Historical'),
                                   store={'product.product': ( lambda
                                       self, cr, uid, ids, c={}: ids, [
                                           'standard_price','historical_ok'], 50), },
                                       help="""Latest Recorded
                                       Historical Cost"""),
            'measure' : fields.selection([
                    ('bandeja', 'BANDEJA'),
                    ('blister', 'BLISTER'),
                    ('bolsa','BOLSA'),
                    ('botella','BOTELLA'),
                    ('bulto','BULTO'),
                    ('caja','CAJA'),
                    ('carton', 'CARTON'),
                    ('display', 'DISPLAY'), 
                    ('docena', 'DOCENA'),
                    ('2pack', 'DUOPACK'),
                    ('exhibidor','EXHIBIDOR'),
                    ('fardo','FARDO'),
                    ('galon', 'GALON'), 
                    ('gramo', 'GRAMO'),
                    ('gruesa', 'GRUESA'),  
                    ('hora', 'HORA'),
                    ('juego','JUEGO'), 
                    ('kilos', 'KILOS'),
                    ('millar','MILLAR'),
                    ('lata','LATA'),
                    ('paila', 'PAILA'),
                    ('saco','SACO'),
                    ('tambor', 'TAMBOR'),
                    ('tarjeta','TARJETA'),
                    ('4pack', 'TETRAPACK'),
                    ('tiras', 'TIRAS'),
                    ('tobo', 'TOBO'),
                    ('tonelada', 'TONELADA'),
                    ('3pack', 'TRIPACK'), 
                    ('unidad', 'UNIDAD'), 
                    ], 'Presentación', help="Especificación de la presentacion del producto"),
             'measure_po' : fields.selection([
                    ('bandeja', 'BANDEJA'),
                    ('blister', 'BLISTER'),
                    ('bolsa','BOLSA'),
                    ('botella','BOTELLA'),
                    ('bulto','BULTO'),
                    ('caja','CAJA'),
                    ('carton', 'CARTON'),
                    ('display', 'DISPLAY'), 
                    ('docena', 'DOCENA'),
                    ('2pack', 'DUOPACK'),
                    ('exhibidor','EXHIBIDOR'),
                    ('fardo','FARDO'),
                    ('galon', 'GALON'), 
                    ('gramo', 'GRAMO'),
                    ('gruesa', 'GRUESA'),
                    ('hora', 'HORA'),
                    ('juego','JUEGO'), 
                    ('kilos', 'KILOS'),
                    ('millar','MILLAR'),
                    ('lata','LATA'),
                    ('paila', 'PAILA'),
                    ('saco','SACO'),
                    ('tambor', 'TAMBOR'),
                    ('tarjeta','TARJETA'),
                    ('4pack', 'TETRAPACK'),
                    ('tiras', 'TIRAS'),
                    ('tobo', 'TOBO'),
                    ('tonelada', 'TONELADA'),
                    ('3pack', 'TRIPACK'), 
                    ('unidad', 'UNIDAD'), 
                    ], 'Presentación', help="Especificación de la presentacion del producto"),
             'pack': fields.char('Empaque', size=20, help="Define en que fraccion se compra, en que fraccion se vende, que medida o tamaño tiene el producto, etc"),
             'sundecop':fields.boolean('Sundecop', help="Indica si el producto esta regulado por el Sundecop"),
             'palette':fields.float('UdV por Paleta', help="Cantidad de unidades de venta que incluye una Paleta"),
             'ind_payment':fields.boolean('Pago independiente', help="Indica que el despacho de este producto se pagará por Bs fijos según la ruta de despacho del cliente. "),
             'historical_ok': fields.boolean('Historico de tarifas actualizado?'),
             'pvm': fields.float('Precio venta marcado', help="Precio de venta marcado (P.V.M.)"),
             'pvp': fields.float('Precio venta al público', help="Precio de venta al publico (P.V.P.)"),
                }
        
    #~ def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		#~ ids=[]
		#~ if not args:
			#~ args=[]
		#~ if not context:
			#~ context={}
		#~ if context and context.has_key('partner_id') and context['partner_id']:
			#~ # Warn: ps.name is the pk of the partner in the product_supplierinfo model
			#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND ps.product_code = %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name))
			#~ res = cr.fetchall()
			#~ ids = map(lambda x:x[0], res)
			#~ if not len(ids):
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND ps.product_name = %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids = map(lambda x:x[0], res)
			#~ if not len(ids):
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND p.ean13 = %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids = map(lambda x:x[0], res)
			#~ if not len(ids):
				#~ if operator in ('like', 'ilike'):
					#~ name='%'+name+'%'
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND ps.product_code '+operator+' %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids = map(lambda x:x[0], res)
				#~ ids = set(ids)
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND ps.product_name '+operator+' %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids.update(map(lambda x:x[0], res))
			#~ if not len(ids):
				#~ if operator in ('like', 'ilike'):
					#~ name='%'+name+'%'
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND p.default_code '+operator+' %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids = map(lambda x:x[0], res)
				#~ ids = set(ids)
				#~ cr.execute('SELECT p.id ' \
					#~ 'FROM product_product AS p ' \
					#~ 'INNER JOIN product_template AS t ' \
					#~ 'ON p.product_tmpl_id=t.id ' \
					#~ 'INNER JOIN product_supplierinfo AS ps ' \
					#~ 'ON ps.product_id=t.id ' \
					#~ 'WHERE ps.name = %s ' \
					#~ 'AND t.name '+operator+' %s ' \
					#~ 'AND t.purchase_ok = True ' \
					#~ 'ORDER BY p.id',
					#~ (context['partner_id'],name ))
				#~ res = cr.fetchall()
				#~ ids.update(map(lambda x:x[0], res))
		#~ if isinstance(ids, set):
			#~ ids = list(ids)
		#~ ids = list(ids)
		#~ if not len(ids):
			#~ ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
		#~ if not len(ids):
			#~ ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
		#~ if not len(ids):
			#~ ids = self.search(cr, user, [('default_code',operator,name)]+ args, limit=limit, context=context)
			#~ ids += self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
			#~ ids = list(set(ids))
		#~ result = self.name_get(cr, user, ids, context)
		#~ return result

    def name_get(self, cr, user, ids, context=None):
        res = super(inherited_product,self).name_get(cr, user, ids, context=context)
        result = []
        for p in res:
            product = self.browse(cr, user, p[0], context=context)
            name = '%s %s'%(p[1],product.pack)
            mytuple = (p[0],name)
            result.append(mytuple)
        return result
    
    _defaults = {
        'uom_id': False,
        'uom_po_id': False,
        'categ_id': False,
        'type': 'product',
        'historical_ok': False,
    }
inherited_product()

class inherited_product_template(osv.osv):
    
    '''Herencia del modelo product.template para agregar campos necesarios en Herrera C.A. '''
    
    _inherit = 'product.template'

    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Product Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user,fleet.group_fleet_manager"),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]
        success = True
        product_obj = self.pool.get('product.product')
        for template in self.browse(cr, uid, ids, context=context):
            product_ids = product_obj.search(cr, uid, [('product_tmpl_id','=',template.id)])
            for product in product_obj.browse(cr, uid, product_ids, context=context):
                qty_available = product.qty_available
                virtual_available = product.virtual_available
                incoming_qty = product.incoming_qty
                outgoing_qty = product.outgoing_qty
                uom_po_id = 'uom_po_id' in vals and vals['uom_po_id']
                if uom_po_id and not (qty_available or virtual_available or incoming_qty or outgoing_qty):
                    vals.pop('uom_po_id')
                    cr.execute('update product_template set uom_po_id=%s where id in %s', (uom_po_id, tuple([template.id]),))
            success = success and super(inherited_product_template,self).write(cr, uid, [template.id], vals, context=context)
        return success
    
    def _check_uom(self, cursor, user, ids, context=None):
        return super(inherited_product_template,self)._check_uom(cursor, user, ids, context=context)
        
    _constraints = [
        (_check_uom, 'Error: La unidad de medida por defecto y la unidad de compra deben ser de la misma categoría. Cambie la unidad de medida por defecto primero y despues proceda a cambiar la de compra.', ['uom_id']),
    ]
    
inherited_product_template()

class inherited_product_uom(osv.osv):
    _inherit = 'product.uom'
    
    _columns = {
            'name': fields.char('Unit of Measure', size=64, required=True, translate=False),
            'measure' : fields.selection([
                    ('bandeja', 'BANDEJA'),
                    ('blister', 'BLISTER'),
                    ('bolsa','BOLSA'),
                    ('botella','BOTELLA'),
                    ('bulto','BULTO'),
                    ('caja','CAJA'),
                    ('carton', 'CARTON'),
                    ('display', 'DISPLAY'), 
                    ('docena', 'DOCENA'),
                    ('2pack', 'DUOPACK'),
                    ('exhibidor','EXHIBIDOR'),
                    ('fardo','FARDO'),
                    ('galon', 'GALON'), 
                    ('gramo', 'GRAMO'),
                    ('gruesa', 'GRUESA'),  
                    ('hora', 'HORA'),  
                    ('juego','JUEGO'), 
                    ('kilos', 'KILOS'),
                    ('millar','MILLAR'),
                    ('lata','LATA'),
                    ('paila', 'PAILA'),
                    ('saco','SACO'),
                    ('tambor', 'TAMBOR'),
                    ('tarjeta','TARJETA'),
                    ('4pack', 'TETRAPACK'),
                    ('tiras', 'TIRAS'),
                    ('tobo', 'TOBO'),
                    ('tonelada', 'TONELADA'),
                    ('3pack', 'TRIPACK'), 
                    ('unidad', 'UNIDAD'), 
                    ], 'Presentación', help="Especificación de la presentacion del producto"),
            }
            
    def onchange_reference(self, cursor, user, ids, uom_type, measure, factor, factor_inv, rounding):
        if not measure or not uom_type:
            return {}
        if uom_type == 'bigger':
            factor_inv = factor_inv > 0.0 and float(factor_inv) or 1.0
            factor = 1.0/float(factor_inv)
            name = '%s / %d Unidades (%.2f)'%(measure.upper(),round(factor_inv,0),round(rounding,2))
        elif uom_type == 'smaller':
            factor = factor > 0.0 and float(factor) or 1.0
            factor_inv = 1.0/float(factor)
            name = '%s / %.2f Unidades (%.2f)'%(measure.upper(),round(factor_inv,2),round(rounding,2))
        else:
            factor = 1
            factor_inv = 1
            name = '%s / 1 Unidad (%.2f)'%(measure.upper(),round(rounding,2))
        return {'value': {'name': name}}
        
    def write(self, cr, uid, ids, vals, context={}):
        if isinstance(ids, (long, int)):
            ids = [ids]
        success = True
        for uom in self.browse(cr, uid, ids, context=context):
            # Comprobamos si se esta modificando la categoria
            category_id = 'category_id' in vals and vals['category_id']
            # Verificamos si esta categoria ya esta asignado a algun producto
            product = self.pool.get('product.product')
            product_ids = product.search(cr,uid,['|',('uom_id','=',uom.id),('uom_po_id','=',uom.id)])
            if category_id and not product_ids:
                # Extraemos la categoria para evitar la validacion 
                # de este campo que se realiza en el super, de 
                # manera que pueda ser posible su modificacion.
                vals.pop('category_id')
                cr.execute('update product_uom set category_id=%s where id in %s', (category_id, tuple([uom.id]),))
            elif product_ids and context.get('product_id', False):
                # Validamos que no pueda ser modificada una unidad de 
                # medida que este asignada a otros productos
                product_ids.remove(context['product_id'])
                for product_brw in product.browse(cr, uid, product_ids, context=context):
                    if product_brw.active:
                        raise osv.except_osv(_('Warning!'),_("No puede modificar una unidad de medida que ya ha se encuentra asignada. Puede verificarlo en el producto '[%s] %s'.") % (product_brw.default_code,product_brw.name))
                        success = False
                        break
            success = success and super(inherited_product_uom, self).write(cr, uid, [uom.id], vals, context)
        return success
        
    def _check_name(self,cr,uid,ids):
        names = [x.name.lower() for x in self.browse(cr, uid, ids, context=context) if x.name and x.id not in ids]
        for self_obj in self.browse(cr, uid, ids, context=context):
            if self_obj.name and self_obj.name.lower() in  names:
                return False
            return True
        
    _sql_constraints = [
        ('product_uom_unique', 'unique(measure,category_id,rounding,factor)', 'Ya existe en sistema una unidad con esta caracteristicas!')
    ]
    #~ 
    #~ _defaults = {
        #~ 'factor': 1.00,
        #~ 'factor_inv': 1.00,
    #~ }
inherited_product_uom()

class inherited_product_category(osv.osv):
    _inherit = 'product.category'

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for categ in self.browse(cr, uid, ids, context=context):
            #we may not know the level of the parent at the time of computation, so we
            # can't simply do res[categ.id] = categ.parent_id.level + 1
            level = 0
            parent = categ.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            res[categ.id] = level
        return res
            
    _columns = {
            'name': fields.char('Name', size=64, required=True, translate=False, select=True),
            'level': fields.function(_get_level, string='Level', type='integer', store=True),
            }
        
inherited_product_category()


class inherited_product_supplierinfo(osv.osv):
    _inherit = 'product.supplierinfo'
    
    _columns = {
        'stat_unit': fields.float('Unidad Estadistica', help="Valoración estadistica del producto emitida por el proveedor"),
    }
inherited_product_supplierinfo()

class inherited_product_historic_price(osv.Model):
    _inherit = "product.historic.price"

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', string='Tarifa'),
        'margin': fields.float('Margen (%)', help="Margen de ganancia. Margen de rentabilidad que se espera obtener de las ventas del producto"),
        'net_price': fields.float('Precio', help="Precio neto de venta. Indica el valor de venta definitivo del producto segun su unidad de venta."),
    }
    
class inherited_product_historic_cost(osv.Model):
    _inherit = "product.historic.cost"

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', string='Tarifa'),
        'discount': fields.float('Descuento', help="Porcentaje de descuento. Indica el descuento lineal a este producto. En caso de no haber descuento dejar en cero (0)"),
        'net_price': fields.float('Costo', help="Precio costo de venta. Indica el costo de compra del producto segun su unidad de venta."),
    }
