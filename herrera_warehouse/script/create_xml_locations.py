# -*- coding: utf-8 -*-
import os
import csv
#~ from xlrd import open_workbook
import xmlrpclib
import re


HOST='localhost'
PORT=8069
DB='replica'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)
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

def obtener_sucursal(EMO):
    sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','ilike','%'+shops[EMO]+'%')])
    return sucursal and sucursal[0] or False

def html_escape(text):
    """Produce entities within text."""
    html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    #~ "'": "&apos;",
    #~ ">": "&gt;",
    #~ "<": "&lt;",
    "á": "&aacute;",
    "é": "&eacute;",
    "í": "&iacute;",
    "ó": "&oacute;",
    "ú": "&uacute;",
    "Á": "&Aacute;",
    "É": "&Eacute;",
    "Í": "&Iacute;",
    "Ó": "&Oacute;",
    "Ú": "&Uacute;",
    }
    return "".join(html_escape_table.get(c,c) for c in text)

def _generate(play):
    if play is True:
        cont = 1
        path_file = '../data/layout.csv'
        view = open('../data/stock_locations.xml','w')
        view.write('<?xml version="1.0" encoding="utf-8"?>\n')
        view.write('<openerp>\n  <data noupdate="0">\n')
        preload = \
        ''''
        <!-- editando data precargada OPENERP-->
        <record id='stock.stock_location_locations' model='stock.location'>
            <field name='name'>UBICACIONES FÍSICAS</field>
        </record>

        <record id='stock.stock_location_company' model='stock.location'>
            <field name='name'>INVENTARIO</field>
        </record>

        <record id='stock.stock_location_locations_partner' model='stock.location'>
            <field name='name'>UBICACIONES DE PARTNERS</field>
        </record>

        <record id='stock.stock_location_suppliers' model='stock.location'>
            <field name='name'>PROVEEDORES</field>
        </record>

        <record id='stock.stock_location_customers' model='stock.location'>
            <field name='name'>CLIENTES</field>
        </record>

        <record id='location_h' model='stock.location'>
            <field name='name'>STOCK BARCELONA</field>
            <field name='location_id' ref = 'stock.stock_location_company'/>
            <field name='usage'>internal</field>
            <field name='chained_location_type'>fixed</field>
            <field name='chained_auto_packing'>transparent</field>
            <field name='active'>True</field>
        </record>

        <record id='stock.stock_location_stock' model='stock.location'>
            <field name='name'>PRINCIPAL BARCELONA</field>
            <field name='location_id' ref = 'location_h'/>
            <field name='chained_location_type'>fixed</field>
            <field name='chained_auto_packing'>transparent</field>
        </record>

        <!-- insertando nueva data HERRERA-->

            <!-- SUCURSAL MARGARITA -->
            <record id='location_d' model='stock.location'>
                <field name='name'>STOCK MARGARITA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>fixed</field>
                <field name='chained_auto_packing'>transparent</field>
                <field name='active'>True</field>
            </record>

            <record id='location_d_principal' model='stock.location'>
                <field name='name'>PRINCIPAL MARGARITA</field>
                <field name='location_id' ref = 'location_d'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>fixed</field>
                <field name='chained_auto_packing'>transparent</field>
                <field name='active'>True</field>
            </record>

            <record id='location_d_entrada' model='stock.location'>
                <field name='name'>ENTRADA MARGARITA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='location_d_alterno' model='stock.location'>
                <field name='name'>ALTERNO MARGARITA</field>
                <field name='location_id' ref = 'location_d'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='location_d_abastecimiento' model='stock.location'>
                <field name='name'>ABASTECIMIENTO MARGARITA</field>
                <field name='location_id' ref = 'location_d'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='location_d_salida' model='stock.location'>
                <field name='name'>SALIDA MARGARITA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>customer</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
                <field name='chained_journal_id'>1</field>
                <field name='chained_picking_type'>out</field>
            </record>

            <record id='location_d_picking' model='stock.location'>
                <field name='name'>PICKING MARGARITA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>fixed</field>
                <field name='chained_location_id' ref='location_d_salida'/>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
                <field name='chained_journal_id'>1</field>
                <field name='chained_picking_type'>out</field>
            </record>

            <!-- SUCURSAL BARCELONA -->

            <record id='location_h_alterno' model='stock.location'>
                <field name='name'>ALTERNO BARCELONA</field>
                <field name='location_id' ref = 'location_h'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='location_h_abastecimiento' model='stock.location'>
                <field name='name'>ABASTECIMIENTO BARCELONA</field>
                <field name='location_id' ref = 'location_h'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='location_h_entrada' model='stock.location'>
                <field name='name'>ENTRADA BARCELONA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>none</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
            </record>

            <record id='stock.stock_location_output' model='stock.location'>
                <field name='name'>SALIDA BARCELONA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>customer</field>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
                <field name='chained_journal_id'>1</field>
                <field name='chained_picking_type'>out</field>
            </record>

            <record id='location_h_picking' model='stock.location'>
                <field name='name'>PICKING BARCELONA</field>
                <field name='location_id' ref = 'stock.stock_location_company'/>
                <field name='usage'>internal</field>
                <field name='chained_location_type'>fixed</field>
                <field name='chained_location_id' ref='stock.stock_location_output'/>
                <field name='chained_auto_packing'>manual</field>
                <field name='active'>True</field>
                <field name='chained_journal_id'>1</field>
                <field name='chained_picking_type'>out</field>
            </record>
        \n'''

        view.write(html_escape(preload))
        archive = csv.DictReader(open(path_file))
        records = []
        for field in archive:

            sucursal = 'location_%s'%field['sucursal']
            pasillo = '%s_%s'%(sucursal,field['pasillo'].zfill(2))
            cara = '%s_%s'%(pasillo,field['cara'].zfill(2))
            nivel = '%s_%s'%(cara,field['nivel'].zfill(2))

            for u in ['pasillo','cara','nivel']:
                if u=='pasillo':
                    location_ref = sucursal not in ['location_h'] \
                    and sucursal or 'stock.stock_location_stock'
                elif u=='cara':
                    location_ref = pasillo
                elif u=='nivel':
                    location_ref = cara
                else:
                    location_ref = 'stock.stock_location_company'

                if eval(u) not in records:
                    view.write("            <record id='%s' model='stock.location'>\n"%eval(u))
                    view.write("                <field name='name'>%s %s</field>\n"%(u.upper(),field[u].zfill(2)))
                    view.write("                <field name='location_id' ref = '%s'/>\n"%location_ref)
                    view.write("                <field name='usage'>internal</field>\n")
                    view.write("                <field name='chained_location_type'>none</field>\n")
                    view.write("                <field name='chained_auto_packing'>manual</field>\n")
                    view.write("                <field name='active'>True</field>\n")
                    view.write("            </record>\n\n")

                    records.append(eval(u))

            cont = cont + 1
        view.write('  </data>\n</openerp>\n')

def __main__():
    print 'Ha comenzado la creacion del archivo'
    _generate(True)
    print 'Ha finalizado la carga de datos'
__main__()
