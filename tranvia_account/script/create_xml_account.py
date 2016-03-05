# -*- encoding: utf-8 -*-
import os
import csv
from xlrd import open_workbook
import xmlrpclib
import re
import math
import time

HOST='localhost'
PORT=8069
DB='replica'
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

def get_parent(code,account_saved):
    ref = 'tranvia_account_%s'%(code[:-1])
    if ref not in account_saved:
        ref = len(code)>1 and get_parent(code[:-1],account_saved) or 'tranvia_account_0'
    return ref
    
def get_internal_type(code,has_child):
    internal_type = 'view'
    if has_child:
        internal_type = 'view'
    elif code[0:3] == '111':
        internal_type = 'liquidity'
    elif code[0:3] == '113':
        internal_type = 'receivable'
    elif code[0:3] == '211':
        internal_type = 'payable'
    else:
        internal_type = 'other'
    return internal_type

    
def get_user_type(code,has_child):
    user_type = 1
    if code[0] == '1':
        user_type = has_child and 12 or 6
    elif code[0] == '2':
        user_type = has_child and 13 or 7
    elif code[0] == '4' or code[0] == '7':
        user_type = has_child and 10 or 8
    elif code[0] == '6' or code[0] == '8':
        user_type = has_child and 11 or 9
    if code[0:2] == '22' and not has_child:
        user_type = 15
    if code[0:3] == '113' and not has_child:
        user_type = 2
    if code[0:3] == '211' and not has_child:
        user_type = 3
    
        
    return user_type
        
def _generate(estado):
    if estado is True:
        path_file = '../data/TRANVIA.csv'
        view = open('../data/account_data.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')   
        view.write('<openerp>\n  <data noupdate="1">\n\n') 
        archive = csv.DictReader(open(path_file))
        print """"
    ########################################################################
    #       ********         LEASE ANTES DE CONTINUAR      **********      #
    #                                                                      #
    # @ No hay instrucciones asociadas                                     #
    #                                                                      #
    ########################################################################
        """
        raw_input("Presione ENTER para continuar o Ctrl+C para cancelar")
        account_saved = []
        account_dict = {}
        view.write("    <record id='tranvia_account_0' model='account.account'>\n")
        view.write("      <field name='code'>0</field>\n")
        view.write("      <field name='parent_id'></field>\n")
        view.write("      <field name='name'>Plan de Cuentas Tranvia</field>\n")
        view.write("      <field name='type'>view</field>\n")
        view.write("      <field name='user_type'>1</field>\n")
        view.write("      <field name='active'>True</field>\n")
        view.write("    </record>\n\n")
        # Almacenamos el archivo en un diccionario
        for field in archive:
            account_dict.update({field["codigo"].replace('"', '').replace("'", '').strip(): field["nombre"].replace('"', '').replace("'", '').strip()})
        
        # Recorremos los elementos del diccionario
        for code in sorted(account_dict.keys()):
            account_ref = 'tranvia_account_%s'%(code)
            account_saved.append(account_ref)
            # Buscamos el padre de la cuenta si el codigo es mayor a un digito
            if len(code) > 1:
                parent_ref = get_parent(code,account_saved)
            else:
                parent_ref = 'tranvia_account_0'
            # Verificamos que la cuenta tenga hijos
            has_child = [child for child in account_dict.keys() if len(child)>len(code) and code in child[:len(code)]] and True or False
            
            # Creamos el record para la cuenta
            view.write("    <record id='tranvia_account_%s' model='account.account'>\n"%(code))
            view.write("      <field name='name'>%s</field>\n"%(account_dict[code]))
            view.write("      <field name='parent_id' eval=\"ref('%s')\"/>\n"%(parent_ref))
            view.write("      <field name='code'>%s</field>\n"%(code))
            view.write("      <field name='type'>%s</field>\n"%(get_internal_type(code,has_child)))
            view.write("      <field name='user_type'>%s</field>\n"%(get_user_type(code,has_child)))
            view.write("      <field name='active'>True</field>\n")
            view.write("    </record>\n\n")

            print 'se ha guardado la cuenta',code
            
        view.write('  </data>\n</openerp>\n')
        
    print """"
    ########################################################################
    #       ********               NOTAS FINALES           **********      #
    #                                                                      #
    # @ Recuerde anadir los archivos account_data.xml en la seccion data   #
    # del __openerp__.py de este modulo(herrera_product)                   # 
    #                                                                      #
    ########################################################################
        """
    raw_input("Presione ENTER para finalizar")

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
