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
            translation_id = object_proxy.execute(DB,uid,PASS,'ir.translation','search',[('lang','=','es_VE'),('name','=','product.template,name'),('res_id','=',i)])
            if translation_id:
                translation = object_proxy.execute(DB,uid,PASS,'ir.translation','read',translation_id[0])
                object_proxy.execute(DB,uid,PASS,'ir.translation', 'write', translation_id, {'source': translation['value']})
                print 'Se actualizo el producto: [%s] %s'%(product['default_code'],product['name'])
            
def __main__():
    print 'Ha comenzado la actualizacion'
    _generate(True)
    print 'Ha finalizado la actualizacion de la tabla'
__main__()
