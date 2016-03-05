# -*- encoding: utf-8 -*-
import os
import csv
import unicodedata
import xmlrpclib
import re
import math

HOST='localhost'
PORT=8069
DB='produccion'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def html_escape(text):
    """Produce entities within text."""
    html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }
    return "".join(html_escape_table.get(c,c) for c in text)

def _generate(estado):
    if estado is True:
        service_ids = object_proxy.execute(DB,uid,PASS,'fleet.service.type','search',[])
        service = object_proxy.execute(DB,uid,PASS,'fleet.service.type','read',service_ids)
        for i in service:
            trn_id = object_proxy.execute(DB,uid,PASS,'ir.translation','search',[('module','=','fleet'),('lang','=','es_VE'),('src','=',i['name'])])
            product_dict = {}
            product_dict['name'] = html_escape(object_proxy.execute(DB,uid,PASS,'ir.translation','read',trn_id[0])['value'])
            if type(product_dict.get('name', False)) == unicode:
                name = unicodedata.normalize('NFKD', product_dict.get('name', False)).encode('ascii','ignore')
            else:
                name = product_dict.get('name', False)
            product_id = object_proxy.execute(DB,uid,PASS,'product.product','search',[('name','=',name.upper())])
            print product_id
            if product_id:
                print 'name: %s, product: %s'%(name.upper(),product_id[0])
                object_proxy.execute(DB,uid,PASS,'fleet.service.type','write',i['id'],{'product_id':product_id[0]})
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
