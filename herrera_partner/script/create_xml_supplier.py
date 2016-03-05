import os
import csv
from xlrd import open_workbook
import xmlrpclib
import re


HOST='localhost'
PORT=8069
DB='testing5'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def obtener_sucursal(EMO):
    shops = { 
        'H':'BARCELONA',
        'D':'MARGARITA',
        'M':'MATURIN',
        'C':'CUMANA',
        'U':'ZULIA',
        'O':'ORDAZ',
        'G':'BOLIVAR',
        'K':'CARUPANO',
        'P':'FALCON',
        }  
    sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','ilike','%'+shops[EMO]+'%')])
    return sucursal and sucursal[0] or False
    
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
        path_file = '../data/Proveedores.txt'
        path_file_two = '../data/Clientes.txt'
        view = open('../data/supplier_data.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n\n') 
        archive = csv.DictReader(open(path_file))
        archive_two = csv.DictReader(open(path_file_two))
        print """"
    ########################################################################
    #       ********         LEASE ANTES DE CONTINUAR      **********      #
    # @ Se obviara el partner Herrera C.A. el cual ya debe haber sido      #
    # cargado en modulo herrera_company (VEJ301936167)                     #
    # @ Se obviaran los partner que no tengan rif                          #
    # @ Se obviaran los partner que no tengan direccion                    #
    ########################################################################
        """
        raw_input("Presione ENTER para continuar o Ctrl+C para cancelar")
        vat_unique = []
        vat_functi = []
        partner_ids = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('customer','=','True')])
        for partner_id in partner_ids:
            value = object_proxy.execute(DB,uid,PASS,'res.partner','read',[partner_id],['vat'])[0]['vat']
            if value not in  vat_unique:
                vat_unique.append(value)
        supplier_saved = []
        country_id = object_proxy.execute(DB,uid,PASS,'res.country','search',[('code','=','VE')])[0]
        shop_id = obtener_sucursal('H')
        for field in archive:
            supplier_dict = {}
            vat = (field["PV5"].replace('"', '').replace("'", '').strip()).split("-")
            vat = 'VE'+''.join(vat)
            if vat not in vat_unique and len(vat)==12:
                vat_unique.append(vat)
                ref = field["PV0"].replace('"', '').replace("'", '').strip()
                try:
                    ref = int(ref)
                except:
                    ref = ref[1:]
                ref = str(ref).zfill(3)
                street = street2 = '%s %s %s' % (field["PV2"].replace('"', '').replace("'", '').strip(),
                                       field["PV3"].replace('"', '').replace("'", '').strip(),
                                       field["PV4"].replace('"', '').replace("'", '').strip(),)
                street = len(street) > 128 and street[:127] or street
                street2 = len(street2) > 128 and street2[127:] or ''
                street = html_escape(street.encode('utf-8', 'ignore'))
                street2 = html_escape(street2.encode('utf-8', 'ignore'))
                if ref not in supplier_saved and len(street)>0:
                    supplier_saved.append(ref)
                    name = html_escape(field["PV1"].replace('"', '').replace("'", '').strip())
                    state_id = []
                    for st in street.split(" "):
                        if not state_id:
                            state_id = object_proxy.execute(DB,uid,PASS,'res.country.state','search',[('name','=',st)])
                    for st in street2.split(" "):
                        if not state_id:
                            state_id = object_proxy.execute(DB,uid,PASS,'res.country.state','search',[('name','=',st)])
                    phone = '0123456781'
                    mobile = '0000000000'
                    view.write("    <record id='res_partner_supplier_%s' model='res.partner' >\n"%str(ref))
                    view.write("      <field name='name'      >%s</field>\n"%str(name))
                    view.write("      <field name='company_id'>%s</field>\n"%str(1))
                    view.write("      <field name='is_company' eval='1'/>\n")
                    view.write("      <field name='street'    >%s</field>\n"%street)
                    view.write("      <field name='vat'       >%s</field>\n"%str(vat) )
                    view.write("      <field name='street2'   >%s</field>\n"%str(street2))
                    view.write("      <field name='country_id'>%s</field>\n"%str(country_id))
                    if state_id:
                        view.write("      <field name='state_id'  >%s</field>\n"%str(state_id[0]))
                    view.write("      <field name='phone'     >%s</field>\n"%str(phone))
                    view.write("      <field name='mobile'    >%s</field>\n"%str(mobile))
                    view.write("      <field name='ref'       >%s</field>\n"%str(ref))
                    view.write("      <field name='shop_id'   >%s</field>\n"%str(shop_id))
                    view.write("      <field name='supplier' eval='1'/>\n")
                    view.write("      <field name='customer' eval='0'/>\n")
                    print 'se ha creado el proveedor ',str(name)
                    view.write("    </record>\n\n")
            elif vat in vat_unique and vat not in vat_functi and len(vat)==12:
                view.write("    <function model=\"res.partner\" name=\"set_supplier\">\n")
                view.write("      <function eval=\"[[('vat', '=', '%s')]]\" model=\"res.partner\" name=\"search\"/>\n"%vat)
                view.write("    </function>\n\n")
                vat_functi.append(vat)
        view.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
