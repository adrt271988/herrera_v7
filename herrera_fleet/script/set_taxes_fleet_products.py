# -*- encoding: utf-8 -*-
import os
import csv
import unicodedata
import xmlrpclib
import re
import math

HOST='localhost'
PORT=8069
DB='servidor'
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
        tax_id = object_proxy.execute(DB,uid,PASS,'account.tax','search',[('account_collected_id','=',451)])[0]
        product_ids = object_proxy.execute(DB,uid,PASS,'product.product','search',[('type','=','service')])
        product = object_proxy.execute(DB,uid,PASS,'product.product','read',product_ids, ['supplier_taxes_id'])
        for p in product:
	    if not p['supplier_taxes_id']:
		object_proxy.execute(DB,uid,PASS,'product.product','write',p['id'],{'supplier_taxes_id':[(6, 0, [tax_id])]})
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
