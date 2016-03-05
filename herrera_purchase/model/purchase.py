# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class purchase_order_line(osv.Model):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"
    
    _columns = {
        'price_unit': fields.float('Real Unit Price', required=True,
                                   digits=(16, 4), help="""Price that will be
                                   used in the rest of
                                   accounting cycle"""),
        'price_base': fields.float('Base Unit Price', required=True,
                                   digits=(16, 2), help="""Price base taken to
                                   calc the discount,
                                   is an informative
                                   price to use it in
                                   the rest of the
                                   purchase cycle like
                                   reference for users"""),
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
    def discount_change(self, cr, uid, ids, product, discount, price_unit,
                        product_qty, partner_id, price_base):
        res = super(purchase_order_line,self).discount_change(cr, uid, ids, 
                    product, discount, price_unit, product_qty, partner_id, price_base)
        return res

    def rpu_change(self, cr, uid, ids, rpu, discount):
        res = super(purchase_order_line,self).rpu_change(cr, uid, ids, rpu, discount)
        return res

    def product_id_change(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        
        if context is None:
            context = {}
        
        shop_obj = self.pool.get('sale.shop')
        pricelist_obj=self.pool.get('product.pricelist')
        product_obj = self.pool.get('product.product')

        # fijamos como unidad base, la unidad de compra ya que para 
        # efectos del branch de herrera la unidad de compra del producto
        # no debe cambiarse al momento de realizar un pedido de compra.
        if product_id:
            prod = product_obj.browse(cr, uid, product_id)
            uom_id = prod.uom_po_id.id
        
        """ Using super to extract result from vauxoo/purchase_discount/purchase_discount.py at line 89"""
        res = super(purchase_order_line,self).product_id_change(cr, uid, 
                          ids, pricelist_id, product_id, qty, uom_id,
                          partner_id, date_order, fiscal_position_id,
                          date_planned, name, price_unit, False)
        
        result = res['value']
        lang = False
        if partner_id:
            lang = self.pool.get('res.partner').read(
                cr, uid, partner_id,['lang'])['lang']
        context['lang'] = lang
        context['partner_id'] = partner_id
        
        if product_id:
            if result.get('price_unit',False):
                price_unit = result['price_unit']
                price_base = price_unit
                discount = 0.0
            else:
                return res
                
            # verificacion del IVA en las sucursales, para la autocarga de impuestos
            taxes = []
            product = product_obj.browse(cr, uid, product_id, context=context)
            shop_id = shop_obj.search(cr,uid,[('warehouse_id','=',context['warehouse_id'])])
            shop_tax = shop_obj.browse(cr,uid,shop_id)[0].tax_iva
            if not shop_tax:
                for tax in product.supplier_taxes_id:
                    if 'IVA' not in tax.name.upper():
                        taxes.append(tax.id)
                result['taxes_id'] = [[6, False, taxes]]
                
            uom_po_id = product.uom_po_id.id or uom_id
            result['product_uom'] = uom_po_id
            result['measure'] = product.measure_po
            result['name'] = '[%s] %s %s' % (product.default_code,product.name,product.pack)
            if res.get('warning',False) and ( \
            res['warning']['message'].find('vende este producto') or \
            res['warning']['message'].find('sells this product') ):
                #elmininamos mensaje de warning innecesario
                res.pop('warning')
            
            if pricelist_id:
                pricelists = pricelist_obj.read(cr,uid,[pricelist_id],['visible_discount'])
                factor_list_price = float(product.uom_id.factor)
                factor_stnd_price = float(product.uom_po_id.factor)
                proporcion = float(factor_stnd_price/factor_list_price)
                price_base = product.standard_price / proporcion
                if(len(pricelists)>0 and pricelists[0]['visible_discount'] and price_base != 0):
                    discount = (price_base - price_unit) / price_base * 100
                    result['discount'] = discount
                result['price_base'] = price_base
                
        return res
