import os
import csv
import xmlrpclib
import re


HOST='localhost'
PORT=28069
DB='herrera_72'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def obtener_sucursal(ccat): 
    EMO = ccat[2:3]
    print 'EMO: ',EMO
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
    
def obtener_employee(rced):

    if rced == '0':
        return ''

    respon = object_proxy.execute(DB,uid,PASS,'hr.employee','search',[('identification_id','ilike','%'+rced+'%')])
    print 'Empleado: ',respon
    return respon and respon[0] or ''

def obtener_category(ccat):
    cat = ccat[0:2]
    category = { 
        'AE':'asset_category_1',
        'AC':'asset_category_2' ,
        'EE':'asset_category_2',
        'MA':'asset_category_3',
        'MB':'asset_category_1',
        'ME':'asset_category_3',
        'TL':'asset_category_7',
        'MA':'asset_category_6',
        'IN':'asset_category_4',
        'TR':'asset_category_5',
        'IS':'asset_category_8',
        'TE':'TERRENOS',
        'TI':'TERRENOS',
        }
    category = category[cat]
    return category and category or ''


def obtener_departament(cdep):
	
	
	if not cdep:
		return ''
	deps = { 
	
		'1':'ADMINISTRACION',
		'01':'ADMINISTRACION',
		'2':'VENTAS CANAL MIXTO', #~ ventas viveres
		'3':'ALMACEN',       #~ almacen viveres
		'4':'INFORMATICA',
		'5':'COMPRAS',
		'6':'LOGISTICA',   #~ operaciones
		'7':'RECURSOS HUMANOS',
		'8':'COMERCIALIZACION', #~ ventas corporativas
		'9':'PRESIDENCIA',
		'10':'CONTABILIDAD',
		'11':'ADMINISTRACION', #~  Administracion principal
		'12':'RECURSOS HUMANOS',    #~ recepcion*
		'13':'SEGURIDAD INTEGRAL',  #~ vigilancia
		'14':'LOGISTICA', #~  taller*
		'15':'TRANSPORTE',
		'16':'SOPORTE/PROCURA', #~ banos
		'17':'SOPORTE/PROCURA',  #~ cuarto de limpieza
		'18':'EXCLUSIVO VARIOS', #~ ventas brahma
		'19':'ALMACEN',            #~  almacen brahma
		'20':'SOPORTE/PROCURA', #~  cocina
		'21':'PRESIDENCIA', #~  vice presidencia
		'22':'PRESIDENCIA',  #~ sala de reunion
		'23':'SOPORTE/PROCURA',  #~ archivo*
		'24':'SOPORTE/PROCURA',  #~ jardin
		'25':'INFORMATICA',      #~ oficina de comunicacion
		'26':'ALMACEN',           #~  banos almacen
		'27':'AUDITORIA INTERNA',  #~ auditoria
		'28':'EXCLUSIVO VARIOS', #~  ventas kraft
		'29':'VENTAS PROCTER',
		'30':'AUDITORIA INTERNA',
		'31':'RECURSOS HUMANOS',  #~ SINTRAHECA
		'32':'SOPORTE/PROCURA',  #~  soporte
		'33':'SEGURIDAD INTEGRAL', #~  departamento S.H.A*
		'34':'PRESIDENCIA', #~  Dpto legal
        }
	dpto = object_proxy.execute(DB,uid,PASS,'hr.department','search',[('name','=',deps[cdep])])
	return dpto and dpto[0] or ''

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
        cont = 1
        path_file = '../data/activos.csv'
        view = open('../data/asset_data.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n') 
        archive = csv.DictReader(open(path_file))
        
        for field in archive:
            print 'Numero: ',cont
            name = html_escape(field["DESCRIP"].replace('"', '').replace("'", '').strip())
            code = html_escape(field["CODIGO"].replace('"', '').replace("'", '').strip())
            seri = html_escape(field["SERIAL1"].replace('"', '').replace("'", '').strip())
            if not seri:
                seri = html_escape(field["SERIAL2"].replace('"', '').replace("'", '').strip())
        
            nsuc = html_escape(field["NOM_SUC"].replace('"', '').replace("'", '').strip())
            cubi = html_escape(field["COD_UBI"].replace('"', '').replace("'", '').strip())
            fcom = html_escape(field["FCOMP"].replace('"', '').replace("'", '').strip())
            tipo = html_escape(field["TIPOACT"].replace('"', '').replace("'", '').strip())
            fden = html_escape(field["FDESIN"].replace('"', '').replace("'", '').strip())
            pcom = float(html_escape(field["PCOMP"].replace('"', '').replace("'", '').strip()))
            dacu = float(html_escape(field["DEPREACU"].replace('"', '').replace("'", '').strip()))
            tdep = int(html_escape(field["TIMEDEP"].replace('"', '').replace("'", '').strip()))
            cdep = html_escape(field["COD_SIT"].replace('"', '').replace("'", '').replace('.', '').strip())
            rced = field["CEDULA"].replace('"', '').replace("'", '').replace(".", '').strip().split("-")
            rced = 'VE'+''.join(rced)
            ncat = html_escape(field["NOM_CAT"].replace('"', '').replace("'", '').strip())
            ccat = html_escape(field["COD_CAT"].replace('"', '').replace("'", '').strip())
            pert = int(html_escape(field["PERTRAN"].replace('"', '').replace("'", '').strip()))
            
            if tipo != 'I':
                view.write("    <record id='account_asset_%s' model='account.asset.asset' >\n"%str(cont))
                view.write("      <field name='name'               >%s</field>\n"%str(name))
                view.write("      <field name='code'               >%s</field>\n"%str(code).zfill(6))
                view.write("      <field name='category_id'        eval=\"ref('%s')\"/>\n"%str(obtener_category(ccat))) 
                view.write("      <field name='serial'             >%s</field>\n"%str(seri))
                view.write("      <field name='shop_id'            >%s</field>\n"%str(obtener_sucursal(ccat)))
                view.write("      <field name='purchase_date'      >%s</field>\n"%str('01/11/2013'))
                view.write("      <field name='date_incorporation' >%s</field>\n"%str('01/11/2013'))
                view.write("      <field name='employee_id' model='hr.employee' search=\"[('vat','=','%s')]\"/>\n"%str(rced)) 
                view.write("      <field name='department_id'      >%s</field>\n"%str(obtener_departament(cdep)))
                view.write("      <field name='purchase_value'     >%f</field>\n"%float(pcom-dacu))
                view.write("      <field name='method'             >%s</field>\n"%str('linear')) 
                view.write("      <field name='method_time'        >%s</field>\n"%str('number')) 
                view.write("      <field name='prorata'            >TRUE</field>\n")
                view.write("      <field name='method_number'      >%d</field>\n"%int(tdep-pert))
                view.write("      <field name='method_period'      >%d</field>\n"%int(1))
                view.write("      <field name='state'              >%s</field>\n"%str('open'))
                view.write("      <field name='date_disincorporate'></field>\n")
                <field search="[('vat','=','VEJ311043314')]" model='res.partner' name='name'/>
                view.write("</record>\n")
            cont = cont + 1
       
        view.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la creacion del archivo'
__main__()
