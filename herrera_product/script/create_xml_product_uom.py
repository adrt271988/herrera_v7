# -*- encoding: utf-8 -*-
import os
import csv
from xlrd import open_workbook
import xmlrpclib
import re
import math

HOST='localhost'
PORT=8069
DB='replica'
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
        path_file = '../data/Productos.txt'
        path_file_two = '../../herrera_partner/data/Proveedores.txt'
        view_pro = open('../data/product_data.xml','w')
        view_uom = open('../data/uom_data.xml','w')
        view_inf = open('../data/supplierinfo_data.xml','w')
        view_pro.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view_uom.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view_inf.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view_pro.write('<openerp>\n  <data noupdate="1">\n\n') 
        view_uom.write('<openerp>\n  <data noupdate="1">\n\n') 
        view_inf.write('<openerp>\n  <data noupdate="1">\n\n') 
        archive = csv.DictReader(open(path_file))
        archive_two = csv.DictReader(open(path_file_two))
        print """"
    ########################################################################
    #       ********         LEASE ANTES DE CONTINUAR      **********      #
    #                                                                      #
    # @ Deben estar registradas las cuentas contables de ingresos y gastos #
    # @ Deben estar registrados los proveedores si desea asignarles sus    #
    #   productos correspondientes                                         #
    # @ No se aceptaran productos sin nombres.                             #
    # @ Se creará un producto unica indiferentemente de la sucursal        #
    # @ Se validará el codigo ean13 si no es valido se le asignará uno     #
    # @ Si tiene productos en su base de datos por favor eliminelos al     #
    #   igual que sus unidades de medidas para asi evitar errores de       #
    #   duplicidad en el momento que se cargue esta data                   #
    # @ Este script sustituira los xml product_data, supplierinfo_data     #
    #   y oum_data del directorio data de este modulo (herrera_product),   #
    #   de ser necesario cancele esta ejecucion y haga el respaldo         #
    #   correspondiente de estos                                           #
    #                                                                      #
    ########################################################################
        """
        raw_input("Presione ENTER para continuar o Ctrl+C para cancelar")
        product_saved = []
        uom_saved = []
        inf_saved = []
        vat_dict = {}
        for line in archive_two:
            ref = line["PV0"].replace('"', '').replace("'", '').strip()
            try:
                ref = int(ref)
            except:
                ref = ref[1:]
            key = str(ref).zfill(3)
            if key not in  vat_dict.keys():
                vat = (line["PV5"].replace('"', '').replace("'", '').strip()).split("-")
                vat_dict[key] = 'VE'+''.join(vat)
                
        for field in archive:
            product_dict = {}
            product_dict['default_code'] = field["PR1"].replace('"', '').replace("'", '').strip()
            product_dict['name'] = html_escape(field["PR4"].replace('"', '').replace("'", '').strip())
            product_dict['list_price'] = float(field["PR5"].replace('"', '').replace("'", '').strip())
            product_dict['standard_price'] = float(field["PR15"].replace('"', '').replace("'", '').strip())
            product_dict['pack'] = field["PR43"].replace('"', '').replace("'", '').strip()
            ean13 = field["PR55"].replace('"', '').replace("'", '').strip()
            product_dict['ean13'] = check_ean(ean13) and ean13 or sanitize_ean13(ean13)
            product_dict['ean14'] = field["PR56"].replace('"', '').replace("'", '').strip()
            product_dict['ean8'] = field["PR57"].replace('"', '').replace("'", '').strip()
            sica = field["PR64"].replace('"', '').replace("'", '').strip()
            sica_id = object_proxy.execute(DB,uid,PASS,'product.sica','search',[('code','=',sica)])
            uom_qty = field["PR42"].replace('"', '').replace("'", '').strip()
            uom_qty = uom_qty > 1.0 and float(uom_qty) or 1.0
            prov_qty = field["PR63"].replace('"', '').replace("'", '').strip()
            prov_qty = prov_qty > 1.0 and float(prov_qty) or 1.0
            measure = str(field["ME1"].replace('"', '').replace("'", '').strip()).zfill(3)
            measure = measure and get_measure(measure) or 'caja'
            uom_ref = 'herrera_uom_%s_%d'%(measure, uom_qty)
            uom_po_ref = 'herrera_uom_%s_%d'%(measure, uom_qty)
            if prov_qty > 1:
                uom_ref = 'herrera_uom_%s_1'%(measure)
                uom_po_ref = 'herrera_uom_%s_%d'%(measure, prov_qty)
            supplier = field["RP0"].replace('"', '').replace("'", '').strip()
            try:
                supplier = int(supplier)
            except:
                supplier = supplier[1:]
            supplier = str(supplier).zfill(3)
            supplier_info = 'product_%s_supplier_%s'%(str(product_dict.get('default_code', False)),supplier)
            
            if uom_ref not in uom_saved:
                view_uom.write("    <record id='%s' model='product.uom' >\n"%(uom_ref))
                view_uom.write("      <field name='name'>%s / %d Unidad(es)</field>\n"%(measure.upper(), prov_qty > 1 and 1 or uom_qty))
                view_uom.write("      <field name='measure'>%s</field>\n"%(measure))
                view_uom.write("      <field name='category_id' eval='ref(\"product.product_uom_categ_unit\")'/>\n")
                view_uom.write("      <field name='uom_type'>%s</field>\n"%(prov_qty > 1.0 and 'reference' or uom_qty == 1.00 and 'reference' or 'bigger'))
                view_uom.write("      <field name='factor'>%f</field>\n"%(1.0/float(prov_qty > 1.0 and 1.0 or uom_qty)))
                #~ view_uom.write("      <field name='factor_inv'>%f</field>\n"%(float(prov_qty > 1.0 and 1.0 or uom_qty)))
                view_uom.write("    </record>\n\n")
                uom_saved.append(uom_ref)
                
            if uom_po_ref not in uom_saved:
                view_uom.write("    <record id='%s' model='product.uom' >\n"%(uom_po_ref))
                view_uom.write("      <field name='name'>%s / %d Unidad(es)</field>\n"%(measure.upper(), prov_qty > 1 and prov_qty or uom_qty))
                view_uom.write("      <field name='measure'>%s</field>\n"%(measure))
                view_uom.write("      <field name='category_id' eval='ref(\"product.product_uom_categ_unit\")'/>\n")
                view_uom.write("      <field name='uom_type'>%s</field>\n"%(prov_qty == 1.0 and uom_qty == 1.0 and 'reference' or 'bigger'))
                view_uom.write("      <field name='factor'>%f</field>\n"%(1.0/float(prov_qty > 1.0 and prov_qty or uom_qty)))
                #~ view_uom.write("      <field name='factor_inv'>%f</field>\n"%(float(prov_qty > 1.0 and 1.0 or uom_qty)))
                view_uom.write("    </record>\n\n")
                uom_saved.append(uom_po_ref)
            
            if str(product_dict.get('name', False)) and str(product_dict.get('default_code', False)) not in product_saved: 
                view_pro.write("    <record id='herrera_product_%s' model='product.product' >\n"%str(product_dict.get('default_code', False)))
                view_pro.write("      <field name='name'>%s</field>\n"%str(product_dict.get('name', False)))
                view_pro.write("      <field name='default_code'>%s</field>\n"%str(product_dict.get('default_code', False)))
                view_pro.write("      <field name='pack'>%s</field>\n"%str(product_dict.get('pack', False)))
                view_pro.write("      <field name='type'>consu</field>\n")
                view_pro.write("      <field name='uom_id' eval='ref(\"%s\")'/>\n"%uom_ref)
                view_pro.write("      <field name='uom_po_id' eval='ref(\"%s\")'/>\n"%uom_po_ref)
                view_pro.write("      <field name='measure'>%s</field>\n"%(measure))
                view_pro.write("      <field name='measure_po'>%s</field>\n"%(measure))
                view_pro.write("      <field name='list_price'>%s</field>\n"%str(product_dict.get('list_price', False))) 
                view_pro.write("      <field name='standard_price'>%s</field>\n"%str(product_dict.get('standard_price', False))) 
                view_pro.write("      <field name='ean13'>%s</field>\n"%str(product_dict.get('ean13', False))) 
                view_pro.write("      <field name='property_account_income'  eval='ref(\"herrera_account.account_ingxventas\")'/>\n")
                view_pro.write("      <field name='property_account_expense'  eval='ref(\"herrera_account.account_gastos5\")'/>\n")
                view_pro.write("      <field name='sica_id'>%s</field>\n"%str(sica_id and sica_id[0] or ''))
                view_pro.write("    </record>\n\n")
                product_saved.append(str(product_dict.get('default_code', False)))
                print 'se ha guardado el producto ',str(product_dict.get('name', False))

                if supplier_info not in inf_saved and supplier in vat_dict.keys() and \
                object_proxy.execute(DB,uid,PASS,'res.partner','search',[('vat','=',vat_dict[supplier])]):
                    view_inf.write("    <record id='herrera_supplierinfo_%s' model='product.supplierinfo'>\n"%str(supplier_info))
                    view_inf.write("      <field search=\"[('vat','=','%s')]\" model='res.partner' name='name'/>\n"%str(vat_dict[supplier]))
                    view_inf.write("      <field name=\"product_id\" eval=\"ref('herrera_product_%s')\"/>\n"%str(product_dict.get('default_code', False)))
                    view_inf.write("      <field name='min_qty'>0</field>\n")
                    view_inf.write("    </record>\n\n")
                    inf_saved.append(supplier_info)

        view_pro.write('  </data>\n</openerp>\n')
        view_uom.write('  </data>\n</openerp>\n')
        view_inf.write('  </data>\n</openerp>\n')
        
    print """"
    ########################################################################
    #       ********               NOTAS FINALES           **********      #
    #                                                                      #
    # @ Recuerde anadir los archivos prodcut_data.xml y uom_data.xml en    #
    #   la seccion data del __openerp__.py de este modulo(herrera_product) #
    #                                                                      #
    ########################################################################
        """
    raw_input("Presione ENTER para finalizar")
def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
