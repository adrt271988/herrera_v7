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
        path_file = 'ciudades.csv'
        view = open('ciudades.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n') 
        
        archive = csv.DictReader(open(path_file))
        for field in archive:
            print 'Numero: ',cont
            name = html_escape(field["name"].replace('"', '').replace("'", '').strip())
            code = html_escape(field["code"].replace('"', '').replace("'", '').strip())
            seri = html_escape(field["zip"].replace('"', '').replace("'", '').strip())
            stat = html_escape(field["state_id"].replace('"', '').replace("'", '').strip())
           
            view.write("<record id='res_country_state_city_%s' model='res.city'>\n"%str(cont))
            view.write("   <field name='name'      >%s</field>\n"%str(name))
            view.write("   <field name='code'      >%s</field>\n"%str(code))
            view.write("   <field name='state_id'  >%s</field>\n"%str(stat)) 
            view.write("</record>\n")
            cont = cont + 1
        view.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la creacion del archivo'
__main__()
