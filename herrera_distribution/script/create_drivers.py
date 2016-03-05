import os
import csv
import xmlrpclib
import re


HOST='localhost'
PORT=8069
DB='db_herrera1'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def obtener_sucursal(ccat): 
    EMO = ccat
    shops = { 
        'H':'BARCELONA',
        'D':'MARGARITA',
        'M':'MATURIN',
        'C':'CUMANA',
        'U':'ZULIA',
        'Z':'ZULIA',
        'O':'ORDAZ',
        'B':'ORDAZ',
        'G':'BOLIVAR',
        'K':'CARUPANO',
        'P':'FALCON',
        'F':'FALCON',
        'A':'SEDE',#sede principal
        }  
    sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','ilike','%'+shops[EMO]+'%')])
    return sucursal and sucursal[0] or ''
    
def obtener_datos_rrhh(ced,rif):
    datos = {}
    if ced and ced != 0 and ced != '0':
        empleado = object_proxy.execute(DB,uid,PASS,'hr.employee','search',[('identification_id','ilike','%'+ced+'%')])
    elif rif:
        rif  = rif.split("-")
        rif = 'VE'+''.join(rif)
        empleado = object_proxy.execute(DB,uid,PASS,'hr.employee','search',[('identification_id','ilike','%'+rif+'%')])
    else:
        empleado = False
    if empleado:
        employee = object_proxy.execute(DB,uid,PASS,'hr.employee','read',empleado[0])

        datos = { 
                'cedula': employee['identification_id'],
                'entry_date': employee['entry_date'],
                'job_id': employee['job_id'][0],
                'department_id': employee['department_id'][0],
                'gender': employee['gender'],
                }
    return datos

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
    
def obtener_cuenta_contable(cod):
    if cod:
        cuenta = object_proxy.execute(DB,uid,PASS,'account.account','search',[('code','=',cod)])
        return cuenta and cuenta[0] or '' 
    return ''
def _generate(estado):
    if estado is True:
        cont = 1
        path_file = '../data/choferes.csv'
        archive = csv.DictReader(open(path_file))
        
        for field in archive:
            nsuc = html_escape(field["OFIC"].replace('"', '').replace("'", '').strip())
            
            ced  = field["CEDULA"].replace('"', '').replace("'", '').replace(".", '').strip()
            rif  = field["RIF"].replace('"', '').replace("'", '').strip()
            
            vals = obtener_datos_rrhh(ced,rif)
            
            rif  = rif.split("-")
            rif = 'VE'+''.join(rif)
            chofer = {
                        'driver_type': html_escape(field["TIPO"].replace('"', '').replace("'", '').strip()),
                        'code': html_escape(field["COD"].replace('"', '').replace("'", '').strip()),
                        'name': html_escape(field["NOMBRE"].replace('"', '').replace("'", '').strip()),
                        'mobile_phone': field["CELULAR"] and html_escape(field["CELULAR"].replace('"', '').replace("'", '').strip()) or html_escape(field["TELEFONO"].replace('"', '').replace("'", '').replace('.', '').strip()),
                        'work_location': nsuc,
                        'department_id': '',
                        'shop_id': obtener_sucursal(nsuc),
                        'job_id': '',
                        'parent_id': '',
                        'country_id': 240,
                        'state_id': obtener_sucursal(nsuc)== 1 and 54 or obtener_sucursal(nsuc)== 2 and 68 or obtener_sucursal(nsuc)== 3 and 70 or obtener_sucursal(nsuc)== 4 and 70 or obtener_sucursal(nsuc)== 5 and 67 or obtener_sucursal(nsuc)== 6 and 75 or obtener_sucursal(nsuc)== 7 and 62 or obtener_sucursal(nsuc)== 8 and 58 or obtener_sucursal(nsuc)== 9 and 58 or obtener_sucursal(nsuc)== 10 and 54 or '',
                        'municipality_id': '',
                        'parish_id': '',
                        'cedula': ced,
                        'rif': rif,
                        'address': html_escape(field["DIRECCION"].replace('"', '').replace("'", '').strip()),
                        'bank_account': html_escape(field["CUENTA_BCO"].replace('"', '').replace("'", '').strip()),
                        'account_payable': obtener_cuenta_contable(field["CUENTA"].replace('"', '').replace("'", '').strip()),
                        'account_receivable': obtener_cuenta_contable(field["CTA_CXP"].replace('"', '').replace("'", '').strip()),
                        'withholding_islr': '',
                        'withholding_iva': '',
                       }
            if vals:
                chofer.update(vals)
            #print chofer
            driver_id = object_proxy.execute(DB,uid,PASS,'fleet.drivers','create',chofer)
            print 'se ha creado el chofer %s ' % object_proxy.execute(DB,uid,PASS,'fleet.drivers','read',[driver_id],["name"])
            cont = cont + 1

            pcom = html_escape(field["COM"].replace('"', '').replace("'", '').strip())
            pret = html_escape(field["RET"].replace('"', '').replace("'", '').strip())

            
            

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la creacion del archivo'
__main__()
