import os
import csv
import xmlrpclib
import re


HOST='localhost'
PORT=28069
DB='produccion-08'
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
        vat = {}
        city = {}
        cities = {}
        state = {}
        states = {}
        path_file = '../data/Adclientes.txt'
        path_file_two = '../data/Clientes.txt'
        path_file_tree = '../data/Zonas.txt'
        path_file_four = '../data/Proveedores.txt'
        vat_unique = []
        country_id = object_proxy.execute(DB,uid,PASS,'res.country','search',[('code','=','VE')])[0]
        archive_two = csv.DictReader(open(path_file_two))
        archive_tree = csv.DictReader(open(path_file_tree))
        for line in archive_tree:
            key = line["ZO1"].replace('"', '').replace("'", '').strip()
            if key not in cities:
                cities[key] = line["ZO2"].replace('"', '').replace("'", '').strip()
                value = line["ZO3"].replace('"', '').replace("'", '').strip().lower()[:2]
                states[key] = value == 'nu' and 'ne' or value in ['gr','dt'] and 'dc' \
                    or value == 'b' and 'bo' or value
        for line in archive_two: 
            key = line["EM0"].replace('"', '').replace("'", '').strip()+line["CLI"].replace('"', '').replace("'", '').strip()
            value = 'VE'+line["CL5"].replace('"', '').replace("'", '').strip()+line["CL6"].replace('"', '').replace("'", '').strip()+line["CL7"].replace('"', '').replace("'", '').strip()
            if value not in  vat_unique:
                city[key] = cities[line["ZO1"].replace('"', '').replace("'", '').strip()]
                state[key] = states[line["ZO1"].replace('"', '').replace("'", '').strip()]
                vat[key] = value
                vat_unique.append(value)
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
        view = open('../data/partners_data.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n\n')
        view.write("    <!-- Clientes de Herrera C.A. --> \n\n")
        archive = csv.DictReader(open(path_file))
        # CARGA DEL ARCHIVO DE CLIENTES
        for field in archive:
            em0 = field["EM0"].replace('"', '').replace("'", '').strip()
            cli = field["CLI"].replace('"', '').replace("'", '').strip()
            ref = em0+cli
            ad1 = html_escape(field["AD1"].replace('"', '').replace("'", '').strip())
            state_id = object_proxy.execute(DB,uid,PASS,'res.country.state','search',[('code','=',state.get(ref,False))])
            if cli != '10000' and vat.get(ref, False) and len(ad1)>0: 
                ad1 = html_escape(field["AD1"].replace('"', '').replace("'", '').strip())
                ad3 = html_escape(field["AD3"].replace('"', '').replace("'", '').strip())
                ad4 = html_escape(field["AD4"].replace('"', '').replace("'", '').strip())
                ad5 = html_escape(field["AD5"].replace('"', '').replace("'", '').strip())
                ad6 = html_escape(field["AD6"].replace('"', '').replace("'", '').strip())
                ad17 = html_escape(field["AD17"].replace('"', '').replace("'", '').strip())
                ad18 = html_escape(field["AD18"].replace('"', '').replace("'", '').strip())
                ad19 = html_escape(field["AD19"].replace('"', '').replace("'", '').strip())
                ad20 = html_escape(field["AD20"].replace('"', '').replace("'", '').strip())
                view.write("    <record id='res_partner_customer_%s' model='res.partner' >\n"%str(ref))
                view.write("      <field name='name'      >%s</field>\n"%str(ad1))
                view.write("      <field name='company_id'>%s</field>\n"%str(1))
                view.write("      <field name='is_company' eval='1'/>\n")
                view.write("      <field name='street'    >%s</field>\n"%str(ad3+(len(ad4)>0 and (', '+ad4) or '')))
                view.write("      <field name='email'     >%s</field>\n"%str(ad20)) 
                view.write("      <field name='vat'       >%s</field>\n"%str(vat[ref])) 
                view.write("      <field name='street2'   >%s</field>\n"%str(ad17+(len(ad18)>0 and (', '+ad18) or '')+(len(ad19)>0 and (', '+ad19) or '')))
                view.write("      <field name='city'      >%s</field>\n"%str(city[ref]))
                view.write("      <field name='country_id'>%s</field>\n"%str(country_id))
                if state_id:
                    view.write("      <field name='state_id'  >%s</field>\n"%str(state_id[0]))
                view.write("      <field name='phone'     >%s</field>\n"%str(ad5))
                view.write("      <field name='mobile'    >%s</field>\n"%str(ad6))
                view.write("      <field name='ref'       >%s</field>\n"%str(cli))
                view.write("      <field name='shop_id'   >%s</field>\n"%str(obtener_sucursal(em0)))
                print 'se ha creado el cliente ',str(ad1)
                view.write("    </record>\n\n")
        
        # CARGA DEL ARCHIVO DE PROVEEDORES
        view.write("\n    <!-- Proveedores de Herrera C.A. --> \n\n")
        customer_saved = vat_unique
        supplier_saved = []
        vat_functi = []
        shop_id = obtener_sucursal('H')
        archive_four = csv.DictReader(open(path_file_four))
        for field in archive_four:
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
            elif vat in customer_saved and vat not in vat_functi and len(vat)==12:
                view.write("    <function model=\"res.partner\" name=\"set_supplier\">\n")
                view.write("      <function eval=\"[[('vat', '=', '%s')]]\" model=\"res.partner\" name=\"search\"/>\n"%vat)
                view.write("    </function>\n\n")
                vat_functi.append(vat)
        view.write('  </data>\n</openerp>\n')



def _update(estado):
    if estado is True:
#~ Funcion para asignar los Municipios y Rutas de Flete a los clientes de Herrera C.A
        path_file = '../data/CLIENTES.csv'
        archive = csv.DictReader(open(path_file))
        cont = 0
        for field in archive:
            ofi = html_escape(field["OFICINA"].replace('"', '').replace("'", '').strip())
            cli = html_escape(field["CLIENTE"].replace('"', '').replace("'", '').strip())
            rut = html_escape(field["RUTA_FLETE"].replace('"', '').replace("'", '').strip())
            mun = html_escape(field["NOMBRE_MUNIC"].replace('"', '').replace("'", '').strip())
            
            shop_id = obtener_sucursal(ofi)
            partner_id = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('ref','=',cli)])
            route = object_proxy.execute(DB,uid,PASS,'freight.route','search',[('shop_id','=',shop_id),('code','=',rut)])
            if route:
                route_id = route[0]
                
            if partner_id:
                partner = object_proxy.execute(DB,uid,PASS,'res.partner','read',partner_id[0])
                state_id = partner['state_id'][0]
                municip_id = object_proxy.execute(DB,uid,PASS,'res.municipality','search',[('state_id','=',state_id),('name','ilike',mun)])
                if municip_id:
                    municipality_id = municip_id[0]
                    object_proxy.execute(DB,uid,PASS,'res.partner', 'write', partner_id, {'municipality_id': municipality_id,'freight_route_id':route_id})
                    cont = cont + 1

        print 'Actualizados: ',cont
                
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(False)
    _update(True)
    print 'Ha finalizado la carga de datos'
__main__()
