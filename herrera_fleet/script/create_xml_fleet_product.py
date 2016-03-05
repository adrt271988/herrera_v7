# -*- encoding: utf-8 -*-
import os
import csv
import unicodedata
import xmlrpclib
import re
import math

HOST='localhost'
PORT=8069
DB='herrera2'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if the string has the wrong length"""
    if len(eancode) <> 13:
        return -1
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    reversevalue = eanvalue[::-1]
    finalean=reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check

def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) <> 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])

def sanitize_ean13(ean13):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean13:
        return "0000000000000"
    ean13 = re.sub("[A-Za-z]","0",ean13);
    ean13 = re.sub("[^0-9]","",ean13);
    ean13 = ean13[:13]
    if len(ean13) < 13:
        ean13 = ean13 + '0' * (13-len(ean13))
    return ean13[:-1] + str(ean_checksum(ean13))

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
def get_measure(code):

    measure_dict = {
        '001':'caja',
        '002':'fardo',
        '003':'saco',
        '004':'3pack',
        '005':'docena',
        '006':'bulto',
        '007':'lata',
        '008':'carton',
        '009':'estuche',
        '010':'unidad',
        '011':'juego',
        '012':'kilos',
        '014':'botella',
        '015':'galon',
        '016':'tiras',
        '017':'bolsa',
        '018':'tobo',
        '019':'display',
        '020':'millar',
        '021':'blister',
        '022':'bandeja',
        '023':'exhibidor',
        '024':'tarjeta',
        '025':'gruesa',
        '026':'tambor',
        '027':'paila',
        '028':'3pack',
        '030':'caja',
    }

    return measure_dict.get(code,False)

def _generate(estado):
    if estado is True:
        services_xml = open('../data/service_data.xml','w')
        services_xml.write('<?xml version="1.0" encoding="utf-8"?>\n')
        services_xml.write('<openerp>\n  <data noupdate="0">\n\n')
        service_ids = object_proxy.execute(DB,uid,PASS,'fleet.service.type','search',[('category','=','service')])
        service = object_proxy.execute(DB,uid,PASS,'fleet.service.type','read',service_ids)
        index = 1
        for i in service:
            trn_id = object_proxy.execute(DB,uid,PASS,'ir.translation','search',[('module','=','fleet'),('lang','=','es_VE'),('src','=',i['name'])])
            product_dict = {}
            product_dict['default_code'] = 'SER'+str(index).zfill(5)
            product_dict['name'] = html_escape(object_proxy.execute(DB,uid,PASS,'ir.translation','read',trn_id[0])['value'])
            uom_ref = 'product.product_uom_hour'
            if type(product_dict.get('name', False)) == unicode:
                name = unicodedata.normalize('NFKD', product_dict.get('name', False)).encode('ascii','ignore')
            else:
                name = product_dict.get('name', False)
            
            services_xml.write("    <record id='herrera_service_%s' model='product.product' >\n"%('S'+str(index)))
            services_xml.write("      <field name='name'>%s</field>\n"%(name.upper()))
            services_xml.write("      <field name='default_code'>%s</field>\n"%str(product_dict.get('default_code', False)))
            services_xml.write("      <field name='type'>service</field>\n")
            services_xml.write("      <field name='measure'>unidad</field>\n")
            services_xml.write("      <field name='measure_po'>unidad</field>\n")
            services_xml.write("      <field name='categ_id' eval='ref(\"product_category_herrera_fleet\")'/>\n")
            services_xml.write("      <field name='uom_id' eval='ref(\"%s\")'/>\n"%uom_ref)
            services_xml.write("      <field name='uom_po_id' eval='ref(\"%s\")'/>\n"%uom_ref)
            services_xml.write("      <field name='property_account_income'  eval='ref(\"herrera_account.account_ingxventas\")'/>\n")
            services_xml.write("      <field name='property_account_expense'  eval='ref(\"herrera_account.account_gastos5\")'/>\n")
            services_xml.write("    </record>\n\n")
            print 'se ha guardado el sevicio ',product_dict.get('name', False)
            index += 1
        services_xml.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
