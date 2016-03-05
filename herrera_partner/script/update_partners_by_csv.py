# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import xmlrpclib
import re
from random import randint
HOST='localhost'
PORT=8069
DB='servidor_4'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)
common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')


###Me logueo
uid = common_proxy.login(DB,USER,PASS)
#### Creo
import csv
Clientes = csv.DictReader(open('../data/Clientes_nuevo.csv'))

def clearup(s, chars='0123456789,;:!@#$%/()?-'):
    return re.sub('[%s]' % chars, '', s).lower()

def obtener_sucursal(EMO,dict_mode=False):
    sucursal = False
    shops = {
        'H':'Barcelona',
        'D':'Margarita',
        'M':'Maturín',
        'C':'Cúmana',
        'U':'Zulia',
        'O':'Puerto Ordaz',
        'G':'Bolívar',
        'K':'Carúpano',
        'P':'Falcón',
        }
    if not dict_mode:
        sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('code','=',EMO)])
    else:
        sucursal = EMO in shops and [shops[EMO]] or sucursal
    return sucursal and sucursal[0]

def find_accounting_partner(partner_id):
    if isinstance(partner_id, list):
        partner_id = partner_id[0]
    partner = object_proxy.execute(DB,uid,PASS,'res.partner','read',partner_id,['is_company','parent_id'])
    while not partner['is_company'] and partner['parent_id']:
        partner = object_proxy.execute(DB,uid,PASS,'res.partner','read',partner['parent_id'][0],['is_company','parent_id'])
    return partner['id']
        
i=1
view = open('log.csv','w')
view.write('OFI,REF,VAT,CLIENTE,ACCION,ID\n')
for field in Clientes:
    if i > 0:
        oficina = field["OFICINA"].replace('"', '').replace("'", '').strip()
        shop_id = obtener_sucursal(oficina)
        name = field["NOMBRE_CLI"].replace('"', '').replace("'", '').strip()
        name = len(name) < 1 and '1 - Nombre desconocido' or name
        ref = field["CLIENTE"].replace('"', '').replace("'", '').strip()
        vat = (field["RIF"].replace('"', '').replace("'", '').strip()).split("-")
        vat_old = (field["RIF"].replace('"', '').replace("'", '').strip()).split("-")
        if len(vat)>1:
            vat[1] = vat[1].zfill(8)
        vat = 'VE'+''.join(vat)
        vat_old = 'VE'+''.join(vat_old)
        street = field["DIRECCION_ENTREGA"].replace('"', '').replace("'", '').strip()
        street2 = field["DIRECCION_FISCAL"].replace('"', '').replace("'", '').strip()
        city = field["NOMBRE_ZONA"].replace('"', '').replace("'", '').strip()
        country_id = object_proxy.execute(DB,uid,PASS,'res.country','search',[('code','=','VE')]) or False
        state_name = field["NOMBRE_ESTADO"].replace('"', '').replace("'", '').strip().title()
        state_id = object_proxy.execute(DB,uid,PASS,'res.country.state','search',[('name','=',state_name)])
        municipality_name = field["NOMBRE_MUNIC"].replace('"', '').replace("'", '').strip().title()
        municipality_name = municipality_name == 'Lic. Diego Baut' and 'Diego Bautista Urbaneja' or municipality_name
        municipality_id = object_proxy.execute(DB,uid,PASS,'res.municipality','search',[('name','=',municipality_name)]) or False
        condition_code = field["TIPO_CONTADO"].replace('"', '').replace("'", '').strip()
        condition_code = condition_code in ['0','1','2','3','4','5'] and condition_code or '1'
        condition_id = object_proxy.execute(DB,uid,PASS,'account.payment.condition','search',[('code','=',condition_code)]) or False
        sica_code = field["CODIGO_SICA"].replace('"', '').replace("'", '').strip()
        category_name = field["NOMBRE_CAT"].replace('"', '').replace("'", '').strip().title()
        category_id = object_proxy.execute(DB,uid,PASS,'res.partner.category','search',[('name','=',category_name)])
        category_id = not category_id and [object_proxy.execute(DB,uid,PASS,'res.partner.category','create',{'name': category_name})] or category_id
        categ = field["NOMBRE_CAT"].replace('"', '').replace("'", '').strip().title()
        credit_limit = float(field["LIMITE_NOR"].replace('"', '').replace("'", '').strip())
        global_limit = float(field["LIMITE_GLO"].replace('"', '').replace("'", '').strip())
        freight_route_code = field["RUTA_FLETE"].replace('"', '').replace("'", '').strip()
        freight_route_id = object_proxy.execute(DB,uid,PASS,'freight.route','search',[('code','=',freight_route_code),('shop_id','=',shop_id)]) or False
        pv_metros = field["METROS"].replace('"', '').replace("'", '').strip()
        pv_islas = field["ISLAS"].replace('"', '').replace("'", '').strip()
        pv_cabezales = field["CABEZALES"].replace('"', '').replace("'", '').strip()
        pv_cajas = field["CAJAS"].replace('"', '').replace("'", '').strip()
        pv_planchas = field["PLANCHAS"].replace('"', '').replace("'", '').strip()
        checkout = field["CHECKOUT"].replace('"', '').replace("'", '').strip()
        telefonos = (field["TELEFONOS"].replace('"', '').replace("'", '').strip()).split("-")
        phone = len(telefonos)>0 and len(telefonos[0])>0 and int(telefonos[0]) > 0 and str(int(telefonos[0])) or False
        mobile = len(telefonos)>1 and len(telefonos[1])>0 and int(telefonos[1]) > 0 and str(int(telefonos[1])) or False
        special = (field["CONTRIB_ESPECIAL"].replace('"', '').replace("'", '').strip())=='S'
        is_company = False
        action = False
        partner_id = False
        c_or_c = ''
        cur_partner = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('ref','=',ref),('shop_id','=',shop_id)])
        partner = {}
        if cur_partner:
            acc_partner  = find_accounting_partner(cur_partner)
            duplicate = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('vat','=',vat),('id','!=',cur_partner[0]),('parent_id','=',False)])
            if acc_partner == cur_partner[0] and not duplicate:
                action = 'write'
                c_or_c = 'cliente'
                # Actualizamos el acc_partner, es decir el partner principal
                partner = { 
                    'supplier_payment_condition': condition_id and condition_id[0], 
                    'payment_condition': condition_id and condition_id[0],
                    'pv_metros': pv_metros, 
                    'street': street, 
                    'freight_route_id': freight_route_id and freight_route_id[0], 
                    'special': special, 
                    'city': city, 
                    'country_id': country_id and country_id[0], 
                    #~ 'property_account_payable': 40, 
                    'parent_id': False,
                    'global_limit': global_limit, 
                    'is_company': True, 
                    'street2': street2, 
                    'state_id': state_id and state_id[0], 
                    'municipality_id': municipality_id and municipality_id[0], 
                    'phone': phone, 
                    'credit_limit': credit_limit, 
                    'checkout': checkout, 
                    'pv_cabezales': pv_cabezales, 
                    'pv_planchas': pv_planchas, 
                    'mobile': mobile, 
                    'ref': ref, 
                    #~ 'property_account_receivable': 28, 
                    'pv_islas': pv_islas, 
                    'shop_id': shop_id, 
                    'vat': vat, 
                    'pv_cajas': pv_cajas, 
                    'category_id': [[6, False, category_id]], 
                    'sica_code': sica_code
                }
                pass
            else:
                action = 'write'
                c_or_c = 'contacto'
                # Actualizamos el contacto
                partner = {
                    'city': city, 
                    'street': street, 
                    'parent_id': acc_partner, 
                    'mobile': mobile, 
                    'type': 'contact', 
                    'country_id': country_id and country_id[0], 
                    'use_parent_address': False, 
                    'phone': phone, 
                    'shop_id': shop_id, 
                    'freight_route_id': freight_route_id and freight_route_id[0], 
                    'street2': street2, 
                    'state_id': state_id and state_id[0], 
                    'municipality_id': municipality_id and municipality_id[0], 
                    'category_id': [[6, False, category_id]], 
                    'ref': ref, 
                    'email': False,
                    'supplier': False
                    }
                if duplicate:
                    partner.update({
                    'is_company':False,
                    'vat':False,
                    'parent_id':duplicate[0],
                    })
                pass
        else:
            cur_partner = object_proxy.execute(DB,uid,PASS,'res.partner','search',['|',('vat','=',vat),('vat','=',vat_old)])
            if cur_partner:
                acc_partner  = find_accounting_partner(cur_partner)
                action = 'create'
                c_or_c = 'contacto'
                # Creamos el contacto
                partner = {
                    'function': False, 
                    'city': city, 
                    'street': street, 
                    'name': name, 
                    'zip': False, 
                    'parent_id': acc_partner, 
                    'mobile': mobile, 
                    'type': 'contact', 
                    'image': False, 
                    'country_id': country_id and country_id[0], 
                    'use_parent_address': False, 
                    'phone': phone, 
                    'shop_id': shop_id, 
                    'freight_route_id': freight_route_id and freight_route_id[0], 
                    'street2': street2, 
                    'state_id': state_id and state_id[0], 
                    'municipality_id': municipality_id and municipality_id[0], 
                    'category_id': [[6, False, category_id]], 
                    'ref': ref, 
                    'email': False,
                    'supplier': False
                }
                pass
            else:
                action = 'create'
                c_or_c = 'cliente'
                # Creamos el partner principal
                partner = { 
                    'supplier_payment_condition': condition_id and condition_id[0], 
                    'payment_condition': condition_id and condition_id[0],
                    'pv_metros': pv_metros, 
                    'street': street, 
                    'freight_route_id': freight_route_id and freight_route_id[0], 
                    'special': special, 
                    'city': city, 
                    'vat': vat, 
                    'country_id': country_id and country_id[0], 
                    #~ 'property_account_payable': 40, 
                    'parent_id': False,
                    'global_limit': global_limit, 
                    'is_company': True, 
                    'street2': street2, 
                    'state_id': state_id and state_id[0], 
                    'municipality_id': municipality_id and municipality_id[0],  
                    'phone': phone, 
                    'credit_limit': credit_limit, 
                    'checkout': checkout, 
                    'pv_cabezales': pv_cabezales, 
                    'pv_planchas': pv_planchas, 
                    'name': name, 
                    'mobile': mobile, 
                    'ref': ref, 
                    #~ 'property_account_receivable': 28, 
                    'pv_islas': pv_islas, 
                    'shop_id': shop_id, 
                    'vat': vat, 
                    'pv_cajas': pv_cajas, 
                    'category_id': [[6, False, category_id]], 
                    'sica_code': sica_code
                }

        try:
            if action == 'write':
                partner_id = cur_partner[0]
                object_proxy.execute(DB,uid,PASS,'res.partner','write',partner_id, partner)
            else:
                partner_id = object_proxy.execute(DB,uid,PASS,'res.partner','create',partner)
                # Aseguramos que el RIF del padre este correcto
                c_or_c == 'contacto' and object_proxy.execute(DB,uid,PASS,'res.partner','write',partner['parent_id'], {'vat':vat})
           
            if ref != '10000':
                p =  object_proxy.execute(DB,uid,PASS,'res.partner','read',partner_id,['name', 'seniat_updated'])
                print  "%d: Se ha %s el %s %s " %(i, action=='write' and 'editado' or 'creado', c_or_c, p['name'])
                if not p['seniat_updated']:
                    print '%d: Actualizando informacion del cliente RIF %s'%(i,vat)
                    object_proxy.execute(DB,uid,PASS,'res.partner', 'update_rif', [partner_id])
        except:
            view.write('%s,%s,%s,%s,%s,%s\n'%(oficina,ref,vat,name,action,partner_id))
    i += 1
