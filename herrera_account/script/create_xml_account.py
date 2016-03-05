# -*- encoding: utf-8 -*-
import os
import csv
#~ from xlrd import open_workbook
import xmlrpclib
import re
import math
import time

HOST='localhost'
PORT=8069
DB='replica_20'
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

def check_account(code):
    xml_id = ''
    lista = [
                {'code': '0', 'name': 'Plan de Cuentas Herrera', 'xml_id': 'account_herrera'},
                {'code': '1', 'name': 'ACTIVO', 'xml_id': 'account_activo'},
                {'code': '11', 'name': 'ACTIVO CIRCULANTE', 'xml_id': 'account_actcirculante'},
                {'code': '13', 'name': 'ACTIVO FIJO', 'xml_id': 'activo_fijo'},
                {'code': '111', 'name': 'CAJA Y BANCO', 'xml_id': 'account_cajabanco'},
                {'code': '11101', 'name': 'CAJA CHICA', 'xml_id': 'account_cajachica'},
                {'code': '11101001', 'name': 'AUX CAJA CHICA', 'xml_id': 'account_auxcajachica'},
                {'code': '113', 'name': 'CUENTAS X COBRAR', 'xml_id': 'account_cxc'},
                {'code': '133', 'name': 'ACTIVOS DEPRECIABLES Y AMORTIZABLES', 'xml_id': 'account_act_dep_amo'},
                {'code': '13301', 'name': 'MOBILIARIO', 'xml_id': 'account_act_mob'},
                {'code': '13302', 'name': 'EQUIPOS ELECTRONICOS', 'xml_id': 'account_act_ee'},
                {'code': '13303', 'name': 'MAQUINARIA Y EQUIPOS', 'xml_id': 'account_act_maq'},
                {'code': '13304', 'name': 'INSTALACIONES', 'xml_id': 'account_act_ins'},
                {'code': '13305', 'name': 'MAQUINARIA AGRICOLA Y MINERA', 'xml_id': 'account_act_maq_agr'},
                {'code': '13307', 'name': 'INMUEBLES', 'xml_id': 'account_act_inm'},
                {'code': '13801', 'name': 'VEHICULOS', 'xml_id': 'account_act_veh_veh'},
                {'code': '13802', 'name': 'VEHICULOS LEASING', 'xml_id': 'account_act_veh_lea'},
                {'code': '13301010', 'name': 'MOBILIARIO', 'xml_id': 'account_act_mob_mob'},
                {'code': '13302010', 'name': 'EQUIPOS ELECTRONICOS', 'xml_id': 'account_act_ee_ee'},
                {'code': '13303010', 'name': 'MAQUINARIA Y EQUIPOS', 'xml_id': 'account_act_maq_maq'},
                {'code': '13304201', 'name': 'DEPRECIACION ACUMULADA INSTALACIONES', 'xml_id': 'account_act_ins_ins'},
                {'code': '13305201', 'name': 'MAQUINARIA AGRICOLA', 'xml_id': 'account_act_maq_agr_min'},
                {'code': '13307101', 'name': 'INMUEBLES (DEPRECIACION)', 'xml_id': 'account_act_inm_inm'},
                {'code': '13801201', 'name': 'VEHICULOS (DEPRECIACION)', 'xml_id': 'account_act_veh_dep'},
                {'code': '13802201', 'name': 'TRANSPORTE LEASING', 'xml_id': 'account_act_veh_veh_lea'},
                {'code': '11301', 'name': 'CUENTAS X COBRAR CLIENTES', 'xml_id': 'account_cxcclientes'},
                {'code': '11301000', 'name': 'CUENTAS X COBRAR CLIENTES', 'xml_id': 'account_cxcclientes_reg'},
                {'code': '115', 'name': 'INVENTARIO', 'xml_id': 'account_inventario'},
                {'code': '11501', 'name': 'INVENTARIOS', 'xml_id': 'account_inventario2'},
                {'code': '11501001', 'name': 'COMPRAS', 'xml_id': 'account_compras'},
                {'code': '11501012', 'name': 'VENTAS', 'xml_id': 'account_ventas'},
                {'code': '11501013', 'name': 'GANANCIAS Y PERDIDAS', 'xml_id': 'account_ganper'},
                {'code': '11502', 'name': 'INVENTARIOS DAÑADO', 'xml_id': 'account_invdanado'},
                {'code': '2', 'name': 'PASIVOS', 'xml_id': 'account_pasivo'},
                {'code': '21', 'name': 'PASIVO CIRCULANTE', 'xml_id': 'account_pascirculante'},
                {'code': '211', 'name': 'EFECTOS Y CUENTAS X PAGAR', 'xml_id': 'account_efecxp'},
                {'code': '21101', 'name': 'EFECTOS X PAGAR', 'xml_id': 'account_exp'},
                {'code': '21102', 'name': 'CXP COMERCIALES', 'xml_id': 'account_cxpcomerciales'},
                {'code': '21102001', 'name': 'CXP PROVEEDORES', 'xml_id': 'account_cxpproveedores'},
                {'code': '4', 'name': 'INGRESOS', 'xml_id': 'account_ingresos'},
                {'code': '41', 'name': 'INGRESOS EN INVENTARIO', 'xml_id': 'account_inginventario'},
                {'code': '411', 'name': 'INGRESOS EN INVENTARIO', 'xml_id': 'account_inginventario2'},
                {'code': '41101001', 'name': 'INGRESOS POR VENTAS', 'xml_id': 'account_ingxventas'},
                {'code': '6', 'name': 'GASTOS', 'xml_id': 'account_gastos'},
                {'code': '61', 'name': 'GASTOS', 'xml_id': 'account_gastos2'},
                {'code': '611', 'name': 'GASTOS', 'xml_id': 'account_gastos3'},
                {'code': '61101', 'name': 'GASTOS', 'xml_id': 'account_gastos4'},
                {'code': '61101001', 'name': 'GASTOS', 'xml_id': 'account_gastos5'},
    ]
    for account in lista:
        if code == account.get('code'):
            xml_id = account.get('xml_id')
    return xml_id

def get_user_type(code, is_view):
    user_type = 1
    if is_view == 'view':
        if code[0] == '1':
            user_type = 12
        if code[0] == '2':
            user_type = 13
        if code[0] == '4' or code[0] == '7':
            user_type = 10
        if code[0] == '6' or code[0] == '8':
            user_type = 11
    else:
        if code[0] == '1':
            user_type = 6
        if code[0:3] == '113':
            user_type = 2
        if code[0] == '2':
            user_type = 7
        if code[0:2] == '22':
            user_type = 15
        if code[0:3] == '211':
            user_type = 3
        if code[0] == '4' or code[0] == '7':
            user_type = 8
        if code[0] == '6' or code[0] == '8':
            user_type = 9
    return user_type

def get_parent(code,account_saved):
    ref = 'herrera_account_%s'%(code[:-1])
    if ref not in account_saved:
        ref = len(code)>1 and get_parent(code[:-1],account_saved) or 'herrera_account_0'
    return ref

def _generate(estado):
    if estado is True:
        path_file = '../data/cuentas.csv'
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
        if check_account('0') == '':
            view.write("    <record id='herrera_account_0' model='account.account'>\n")
            view.write("      <field name='code'>0</field>\n")
            view.write("      <field name='parent_id'></field>\n")
            view.write("      <field name='name'>Plan de Cuentas Herrera</field>\n")
            view.write("      <field name='type'>view</field>\n")
            view.write("      <field name='user_type'>1</field>\n")
            view.write("      <field name='active'>True</field>\n")
            view.write("    </record>\n\n")
        # Almacenamos el archivo en un diccionario
        for field in archive:
            account_dict.update({field["CU0"].replace('"', '').replace("'", '').strip(): field["CU2"].replace('"', '').replace("'", '').strip()})

        # Recorremos los elementos del diccionario
        for code in sorted(account_dict.keys()):
            account_ref = 'herrera_account_%s'%(code)
            account_saved.append(account_ref)
            # Buscamos el padre de la cuenta si el codigo es mayor a un digito
            if len(code) > 1:
                if check_account(code) == '':
                    parent_ref = get_parent(code,account_saved)
                else:
                    parent_ref = check_account(code)
            else:
                parent_ref = 'account_herrera'
            # Verificamos que la cuenta tenga hijos
            if check_account(code) == '':
                is_view = [child for child in account_dict.keys() if len(child)>len(code) and code in child[:len(code)]] and 'view' or 'other'
                view.write("    <record id='herrera_account_%s' model='account.account'>\n"%(code))
                view.write("      <field name='name'>%s</field>\n"%(account_dict[code] and html_escape(account_dict[code]) or code))
                view.write("      <field name='parent_id' eval=\"ref('%s')\"/>\n"%(parent_ref))
                view.write("      <field name='code'>%s</field>\n"%(code))
                view.write("      <field name='type'>%s</field>\n"%(is_view))
                view.write("      <field name='user_type'>%d</field>\n"%(get_user_type(code,is_view)))
                view.write("      <field name='active'>True</field>\n")
                view.write("    </record>\n\n")

            print 'se ha guardado la cuenta',code

        view.write('  </data>\n</openerp>\n')

    print """"
    ########################################################################
    #       ********               NOTAS FINALES           **********      #
    #                                                                      #
    # @ Recuerde anadir los archivos account_data.xml en la seccion data   #
    # del __openerp__.py de este modulo(herrera_account)                   #
    #                                                                      #
    ########################################################################
        """
    raw_input("Presione ENTER para finalizar")

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
