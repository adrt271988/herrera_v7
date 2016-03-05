import os
import csv
import xmlrpclib
import re


HOST='localhost'
PORT=8069
DB='piloto'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def _generate(estado):
    if estado is True:

        product_ids = object_proxy.execute(DB,uid,PASS,'product.product','search',[('active','=',True),('type','=','product')])

        for i in product_ids:
            product = object_proxy.execute(DB,uid,PASS,'product.product','read',i)
            income = product['property_account_income']
            expense = product['property_account_expense']
            product_tmpl_id = product['product_tmpl_id'][0]
            if not income or not expense:
                object_proxy.execute(DB,uid,PASS,'product.template', 'write',[product_tmpl_id], {'property_account_income': 830, 'property_account_expense': 31 })
                print 'Se actualizo el producto: [%s] %s'%(product['default_code'],product['name'])
            
def __main__():
    print 'Ha comenzado la actualizacion'
    _generate(True)
    print 'Ha finalizado la actualizacion de la tabla'
__main__()
