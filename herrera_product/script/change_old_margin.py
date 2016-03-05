# -*- coding: utf-8 -*-
import os
import csv
#~ from xlrd import open_workbook
import xmlrpclib
import re
import time
import datetime

HOST='localhost'
PORT=8069
DB='produccion'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)
shops = {
        'H':'Barcelona',
        'D':'Margarita',
        'M':'Maturín',
        'C':'Cúmana',
        'U':'Zulia',
        'O':'Puerto Ordaz',
        'G':'Bolívar',
        'K':'Carúpano',
        'P':'Falcón',
        }

def obtener_sucursal(EMO):
    sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','ilike','%'+shops[EMO]+'%')])
    return sucursal and sucursal[0] or False

def html_escape(text):
    """Produce entities within text."""
    html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    #~ "'": "&apos;",
    #~ ">": "&gt;",
    #~ "<": "&lt;",
    "á": "&aacute;",
    "é": "&eacute;",
    "í": "&iacute;",
    "ó": "&oacute;",
    "ú": "&uacute;",
    "Á": "&Aacute;",
    "É": "&Eacute;",
    "Í": "&Iacute;",
    "Ó": "&Oacute;",
    "Ú": "&Uacute;",
    }
    return "".join(html_escape_table.get(c,c) for c in text)
    
def get_pricelist_name(num,suc):
    return 'Tarifa de Venta %s - %s'%(num,suc)
    
def _generate(play):
    if play is True:
        cont = 1
        path_file = '../data/margenes_201114.csv'
        archive = csv.DictReader(open(path_file))
        product_map = []
        this_date = time.strftime('%Y-%m-%d')
        for field in archive:
            product_map.append({'su':field['sucursal'],
                                'co':field['codigo'],
                                'uc':field['uc'],
                                'p1':field['p1'],
                                'p2':field['p2'],
                                'p3':field['p3'],
                                'm1':field['m1'],
                                'm2':field['m2'],
                                'm3':field['m3'],
            })
            #~ print 'S=%s, C=%s, P1=%s, P2=%s, P3=%s, CP=%s, UC=%s, M1=%s, M2=%s, M3=%s'%()
        for num in [3,2,1]:
            for su in shops:
                name = get_pricelist_name(num,shops[su])
                pricelist_id = object_proxy.execute(DB,uid,PASS,'product.pricelist','search',[('name','=',name)])
                 # verificamos la version activa de la tarifa.
                if pricelist_id:
                    pricelist_version_ids = object_proxy.execute(DB,uid,PASS,'product.pricelist.version','search',[
                                            ('pricelist_id', '=', pricelist_id[0]),
                                            '|',
                                            ('date_start', '=', False),
                                            ('date_start', '<=', this_date),
                                            '|',
                                            ('date_end', '=', False),
                                            ('date_end', '>=', this_date),
                                        ])
                    if pricelist_version_ids:
                        products = [{'id':object_proxy.execute( \
                        DB,uid,PASS,'product.product','search', \
                        ['|',('default_code','=',x['co']), \
                         ('default_code','=',x['co'].zfill(7))])[0],
                        'margin':float(x['m%s'%str(num)]), \
                        'price':float(x['p%s'%str(num)]), 
                        'cost':float(x['uc']), \
                        'code':x['co']} \
                        for x in product_map if x['su'] == su and \
                         object_proxy.execute(DB,uid,PASS, \
                         'product.product','search', \
                         ['|',('default_code','=',x['co']), \
                         ('default_code','=',x['co'].zfill(7))])]
                        for product in products:
                            margin = product['margin'] > 0.00 and product['margin'] < 100.00 and ( product['margin'] / 100.00 ) or 0.00
                            if margin == 0.00:
                                cost = product['cost'] > 0.00 and product['cost'] or object_proxy.execute( DB,uid,PASS,'product.product','read', product['id'], ['standard_price'] )['standard_price']
                                margin = product['price'] > 0.00 and cost > 0.00 and (1.0 - ( cost / product['price'] ) ) or 0.00
                            item_ids = object_proxy.execute(DB,uid,PASS,'product.pricelist.item','search',[('price_version_id','=',pricelist_version_ids[0]),('product_id','=',product['id'])])
                            if item_ids:
                                object_proxy.execute(DB,uid,PASS,'product.pricelist.item','write', item_ids, {'price_discount': margin })
                            else:
                                object_proxy.execute(DB,uid,PASS,'product.pricelist.item','create',{'min_quantity':0.00,
                                                        'price_discount': margin,
                                                        'name':product['code'],
                                                        'product_id':product['id'],
                                                        'base': 2,
                                                        'price_version_id':pricelist_version_ids[0],
                                                        'sequence':1,
                                                        'price_round':0.00,
                                                        'price_min_margin':0.00,
                                                        'price_max_margin':0.00,
                                                        'price_surcharge':0.00,
                                                })
                            print 'Actualizado margen de producto %s en %s '%(product['code'],name)

            
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
