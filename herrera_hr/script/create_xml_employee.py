import os
import csv
from xlrd import open_workbook
import xmlrpclib
import re
from datetime import datetime

HOST='localhost'
PORT=8069
DB='desarrollo3'
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

def obtener_departament(dpto):
    if 'PRESIDENCIA' == dpto:
        departament = '1'
    elif 'AUDITORIA INTERNA' == dpto:
        departament = '2'
    elif 'ADMINISTRACION' == dpto:
        departament = '3'
    elif 'CONTABILIDAD' == dpto:
        departament = '4'
    elif 'RECURSOS HUMANOS' == dpto:
        departament = '5'
    elif 'INFORMATICA' == dpto:
        departament = '6'
    elif 'COMERCIALIZACION' == dpto:
        departament = '7'
    elif 'COMPRAS' == dpto:
        departament = '8'
    elif 'LOGISTICA' == dpto:
        departament = '9'
    elif 'SOPORTE/PROCURA' == dpto:
        departament = '10'
    elif 'SEGURIDAD INTEGRAL' == dpto:
        departament = '11'
    elif 'EXCLUSIVO VARIOS' == dpto:
        departament = '12'
    elif 'VENTAS PROCTER & GAMBLE' == dpto:
        departament = '13'
    elif 'VENTAS CANAL MIXTO' == dpto:
        departament = '14'
    elif 'ALMACEN' == dpto:
        departament = '15'
    elif 'TRANSPORTE' == dpto:
        departament = '16'
    elif "TRADE MARKETING KELLOGS" == dpto:
        departament = '17'
    else:
        departament = ''
            
    return departament 
     
def _generate(estado):
    if estado is True:
        ci_unique = []
        cargo_unique = []
        path_file = '../data/empleados.csv'
        view = open('../data/employee_data.xml','w')
        view_job = open('../data/job_data.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view_job.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n') 
        view_job.write('<openerp>\n  <data noupdate="1">\n') 
        archive = csv.DictReader(open(path_file))
        for field in archive:
            nombre = field["TrabajadorNombre"].replace('"', '').replace("'", '').strip()
            apellido = field["TrabajadorApellido"].replace('"', '').replace("'", '').strip()
            codigo = field["Codigo"].replace('"', '').replace("'", '').strip()
            ci = (field["CI"].replace('"', '').replace("'", '').replace('.', '').strip()).split("-")
            ci = 'VE'+''.join(ci)
            sexo = field["Sexo"].replace('"', '').replace("'", '').strip() == 'M' and 'male' or 'female'
            rif = (field["RIF"].replace('"', '').replace("'", '').replace('.', '').strip()).split("-")
            rif = 'VE'+''.join(rif)
            fecha = field["FechaIngreso"].replace('"', '').replace("'", '').strip()
            shop = field["Sucursal"].replace('"', '').replace("'", '').strip()
            shop = shop == 'SEDE' and 'BARCELONA' or shop
            sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','ilike','%'+shop+'%')])
            dep = field["Departamento"].replace('"', '').replace("'", '').strip()
            car = field["Cargo"].replace('"', '').replace("'", '').replace(".", '').strip()
            cargo = car.replace(' ', '_').lower()
            if cargo not in cargo_unique:
                view_job.write("    <record id='herrera_job_%s' model='hr.job' >\n"%str(cargo))
                view_job.write("      <field name='name'>%s</field>\n"%str(car))
                if obtener_departament(dep):
                    view_job.write("      <field name='department_id' eval='ref(\"hr_department_%s\")' />\n"%str(obtener_departament(dep)))
                view_job.write("    </record>\n")
                cargo_unique.append(cargo)
                print 'se ha creado el cargo ',str(car)
            if ci not in ci_unique and len(ci)>6:
                ci_unique.append(ci)
                view.write("    <record id='herrera_employee_%s' model='hr.employee' >\n"%str(ci))
                view.write("      <field name='name'>%s</field>\n"%str(nombre + ' ' + apellido))
                view.write("      <field name='shop_id'>%s</field>\n"%str(sucursal and sucursal[0] or ''))
                if obtener_departament(dep):
                    view.write("      <field name='department_id' eval='ref(\"hr_department_%s\")' />\n"%str(obtener_departament(dep)))
                view.write("      <field name='job_id' eval='ref(\"herrera_job_%s\")' />\n"%str(cargo))
                view.write("      <field name='identification_id'>%s</field>\n"%str(ci))
                view.write("      <field name='passport_id'>%s</field>\n"%str(rif))
                view.write("      <field name='otherid'>%s</field>\n"%str(codigo))
                view.write("      <field name='gender'>%s</field>\n"%str(sexo))
                view.write("      <field name='entry_date'>%s</field>\n"%datetime.strptime(str(fecha), '%d/%m/%Y').strftime('%Y-%m-%d'))
                view.write("    </record>\n")
                print 'se ha creado el empleado ',str(nombre + ' ' + apellido+' - '+ci)
        view.write('  </data>\n</openerp>\n')
        view_job.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
