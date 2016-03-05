# -*- encoding: utf-8 -*-
import os
import csv
#~ from xlrd import open_workbook
import xmlrpclib
import re
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta

HOST='localhost'
PORT=8069
DB='bd7'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

# ATENCION!!!!! Listado de cableos:
default_purchase_pricelist = 2 # tarifa de compra por defecto
company_id = 1 # herrera c.a.
warehouse_id = 1 # almacen barcelona
max_order_lines = 80 # maximo de lineas por pedido de compra
fix_qty = 60 # cantidad fija a pedir de cada producto

def planned_date(delay=0.0):
    po_lead = object_proxy.execute(DB,uid,PASS,'res.company','read',company_id,['po_lead'])['po_lead']
    date_planned = datetime.today() - relativedelta(days=po_lead)
    if delay:
        date_planned -= relativedelta(days=delay)
    return date_planned and date_planned.strftime('%Y-%m-%d %H:%M:%S') or False
        
def _generate(estado):
    if estado is True:
        categ_id = object_proxy.execute(DB,uid,PASS,'res.partner.category','search',[('name','=','COMPRAS')])
        location_id = object_proxy.execute(DB,uid,PASS,'stock.warehouse','read',warehouse_id,['lot_input_id'])['lot_input_id'][0]
        supplier_ids = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('supplier','=',True),('active','=',True),('category_id','in',categ_id)])
        suppliers = object_proxy.execute(DB,uid,PASS,'res.partner','read',supplier_ids, ['name','category_id','property_product_pricelist_purchase'])
        cont = 1
        for s in suppliers:
            partner_id = s['id']
            #~ pricelist_id = s['property_product_pricelist_purchase'] and s['property_product_pricelist_purchase'][0] or default_purchase_pricelist
            supplierinfo_ids = object_proxy.execute(DB,uid,PASS,'product.supplierinfo','search',[('name','=',s['id'])])
            supplierinfos = object_proxy.execute(DB,uid,PASS,'product.supplierinfo','read',supplierinfo_ids,['product_id'])
            purchase_lines = []
            purchase = {
                'origin': 'WEB/%s'%str(cont).zfill(3),
                'partner_id': partner_id,
                'pricelist_id': default_purchase_pricelist,
                'company_id': company_id,
                'location_id':location_id,
                'warehouse_id':warehouse_id,
            }
            print purchase['origin']
            print s['name']
            cont_line = 0
            for info in supplierinfos:
                product = object_proxy.execute(DB,uid,PASS,'product.product','read',info['product_id'][0],['name','default_code','uom_po_id','standard_price','measure_po','active'])
                product_id = product['id']
                product_name = '[%s] %s'%(product['default_code'],product['name'])
                product_uom = product['uom_po_id'][0]
                product_mea = product['measure_po']
                product_qty = fix_qty
                price_unit = product['standard_price']
                #~ price_unit = object_proxy.execute(DB,uid,PASS,'product.pricelist','price_get', [pricelist_id], product_id, product_qty, {'uom': product_uom})
                purchase_line = {
                    'name': '[%s] %s'%(product['default_code'],product['name']),
                    'product_qty': product_qty,
                    'product_id': product['id'],
                    'product_uom': product['uom_po_id'][0],
                    'price_unit': price_unit,
                    'price_base': price_unit,
                    'date_planned': planned_date(),
                    'measure': product_mea,
                }
                if price_unit > 0.0 and product['active']:
                    purchase_lines.append((0,0,purchase_line))
                    cont_line += 1
                if cont_line == max_order_lines:
                    purchase.update({'order_line':purchase_lines})
                    if len(purchase_lines) > 0:                    
                        p = object_proxy.execute(DB,uid,PASS,'purchase.order','create',purchase)
                        print  "se ha creado %s " % object_proxy.execute(DB,uid,PASS,'purchase.order','read',[p],['name'])
                    purchase_lines = []
                    cont_line = 0
            cont+=1
            purchase.update({'order_line':purchase_lines})
            if len(purchase_lines) > 0:
                p = object_proxy.execute(DB,uid,PASS,'purchase.order','create',purchase)
                print  "se ha creado %s " % object_proxy.execute(DB,uid,PASS,'purchase.order','read',[p],['name'])
        #~ print cont
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
