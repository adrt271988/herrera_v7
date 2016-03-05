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
from time import sleep
HOST='localhost'
PORT=8069
DB='servidor'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)
common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')

#######create
#######write
#######read


###Me logueo
uid = common_proxy.login(DB,USER,PASS)
#### Creo
import csv
Vendedores = csv.DictReader(open('../data/vendedores.csv'))
Rutas = csv.DictReader(open('../data/Rutas_Nuevo.csv'))
P={}
A={}
V={}
S={}
E={}

def is_VE_phone(number):
    operador = ['0412','0422','0414','0424','0416','0426','0212','0234','0235','0237','0238',
                '0239','0240','0241','0242','0243','0244','0245','0246','0247','0248','0249',
                '0251','0252','0253','0254','0255','0256','0257','0258','0259','0261','0262',
                '0263','0264','0265','0266','0267','0268','0269','0271','0272','0273','0274',
                '0275','0276','0277','0278','0279','0281','0282','0283','0284','0285','0286',
                '0287','0288','0289','0291','0292','0293','0294','0295']
    if number[0:4] in operador:
        return True
    return False

def clearup(s, chars='0123456789,;:!@#$%/()?-'):
    return re.sub('[%s]' % chars, '', s).lower()

def limpiar_nombre_vendedor(VE2):
    ven = VE2.replace('"', '').replace("'", '')
    ven_list = [clearup(i).capitalize() for i in ven.split(' ') \
                if len(clearup(i))>0 and clearup(i) \
                not in ['tlf','telefono','telef','tel'] ]
    nombre = ''
    for i in range(len(ven_list)):
        nombre += ven_list[i]+' '
    nombre = len(nombre)<3 and 'Vendedor sin nombre' or nombre.rstrip()
    pos_punto = nombre.count('.') and nombre.index('.') or 0
    if pos_punto and pos_punto<(len(nombre)-1) and nombre[pos_punto+1]!=' ':
        nombre = nombre.replace(nombre[pos_punto+1],' %s'%(nombre[pos_punto+1].upper()))
    deny = [
            'Vacante', 
            'Casa', 
            'Oficina', 
            'Tiendas', 
            'Mercal', 
            'Contado', 
            'Vendedor', 
            'Nombre', 
            'Ventas', 
            'Procter', 
            'Supervisor'
    ]
    for d in deny:
        if d.lower() in nombre.lower():
            nombre = False
            break
    return nombre

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

def get_pricelist(num,suc):
    name = 'Tarifa de Venta %s - %s'%(num,obtener_sucursal(suc,True))
    pricelist_id = object_proxy.execute(DB,uid,PASS,'product.pricelist','search',[('name','=',name)])
    return pricelist_id and pricelist_id[0] or False

ven = False
plan = {}
plan_id = []
attendance_ids = []
vendedores = {}
supervisores = {}
tipos = {}
print 'Procesando usuarios...'
for Vendedor in Vendedores:
    sucursal = Vendedor['oficina'].replace('"', '').replace("'", '')
    name = limpiar_nombre_vendedor(Vendedor['vendedor'])
    codigo = Vendedor['cven'].replace('"', '').replace("'", '').zfill(2)
    ven = (sucursal+codigo).lower()
    vlogin = 'vtas%s'%ven
    supervisor = limpiar_nombre_vendedor(Vendedor['supervisor'])
    scodigo = Vendedor['csup'].replace('"', '').replace("'", '').zfill(2)
    sup = (sucursal+Vendedor['csup']).lower()
    slogin = 'super%s'%sup
    tipo = Vendedor['tipo'].replace('"', '').replace("'", '')
    if sucursal == 'H' and int(codigo)<50:
        #~ print 'sucursal',sucursal
        #~ print 'login',login
        #~ print 'vendedor',name
        #~ print 'codigo',codigo
        #~ print 'tipo',tipo
        #~ print 'supervisor',supervisor
        #~ print 'scodigo',scodigo
        #~ print '---------------------------------'
        v = object_proxy.execute(DB,uid,PASS,'res.users','search',[('login','=',vlogin)])
        v = v and v[0] or False
        if not v and name:
            V.update({'name':name,'login':vlogin,'password': '12345','shop_id': obtener_sucursal(sucursal),'lang':'es_VE'})
            v = object_proxy.execute(DB,uid,PASS,'res.users','create',V)
            print  "se ha creado %s " % object_proxy.execute(DB,uid,PASS,'res.users','read',[v],['name'])
        vendedores.update({ven:v})
        s = object_proxy.execute(DB,uid,PASS,'res.users','search',[('login','=',slogin)])
        s = s and s[0] or False
        if not s and supervisor:
            S.update({'name':supervisor,'login':slogin,'password': '12345','shop_id': obtener_sucursal(sucursal),'lang':'es_VE'})
            s = object_proxy.execute(DB,uid,PASS,'res.users','create',S)
            print  "se ha creado %s " % object_proxy.execute(DB,uid,PASS,'res.users','read',[s],['name'])
        supervisores.update({ven:s})
        tipos.update({ven:tipo})
        #~ sleep(0.3)
print 'Procesando planificaciones...'
for Ruta in Rutas:
    sucursal = 'H'
    codigo = Ruta["VENDEDOR_RUTA"].strip().zfill(2)
    ref = Ruta["CLIENTE"].strip()
    usuario = False
    shop_id = obtener_sucursal(sucursal)
    
    if not object_proxy.execute(DB,uid,PASS,'sale.plan','search',[('code','=',codigo),('shop_id','=',shop_id)]):
        p = { 
             'code' : codigo,
             'user_id' : usuario,
             'shop_id' : shop_id,
             'frequency': 'weekly',
            }
        #~ if not usuario:
            #~ p.update({'name' : 'VACANTE %s%s'%(sucursal,codigo)})
        #~ else:
            #~ p.update({'name' : 'VENDEDOR %s%s'%(sucursal,codigo)})
        p.update({'name' : 'VENDEDOR %s%s'%(sucursal,codigo)})
        new_plan_id = object_proxy.execute(DB,uid,PASS,'sale.plan','create',p)
        print  "se ha creado %s " % object_proxy.execute(DB,uid,PASS,'sale.plan','read',new_plan_id,['name'])
    
    if not ven:
        ven = sucursal+codigo
        shop_id = obtener_sucursal(sucursal)
        plan_id = object_proxy.execute(DB,uid,PASS,'sale.plan','search',[('code','=',codigo),('shop_id','=',shop_id)])
        plan = plan_id and object_proxy.execute(DB,uid,PASS,'sale.plan','read',plan_id,['name','attendance_ids'])[0] or {}
        
    if ven and ven != sucursal+codigo:
            #~ raw_input("Press Enter to continue...")
        if plan_id and attendance_ids:
            object_proxy.execute(DB,uid,PASS,'sale.plan','write',plan_id,{'attendance_ids': attendance_ids})
            print  "se ha editado %s " % object_proxy.execute(DB,uid,PASS,'sale.plan','read',plan_id,['name'])
        shop_id = obtener_sucursal(sucursal)
        plan_id = object_proxy.execute(DB,uid,PASS,'sale.plan','search',[('code','=',codigo),('shop_id','=',shop_id)])
        plan = plan_id and object_proxy.execute(DB,uid,PASS,'sale.plan','read',plan_id,['name','attendance_ids'])[0] or {}
        ven = sucursal+codigo
        attendance_ids = []

    partner_id = len(ref)>0 and object_proxy.execute(DB,uid,PASS,'res.partner','search',[("ref","=",ref),("shop_id","=",shop_id)])

    if plan and 'attendance_ids' in plan and len(plan['attendance_ids'])==0 and partner_id:
        attendance={
                'name':Ruta["CLIENTE"].strip(),
                'partner_id': partner_id[0],
                'boletin': Ruta["APLICA_BOLET"].strip() == 'S',
                'dayofweek': Ruta["DIA"].strip()== 'LU' and '0' or Ruta["DIA"].strip()== 'MA' and '1' or Ruta["DIA"].strip()== 'MI' and '2' or Ruta["DIA"].strip()== 'JU' and '3' or Ruta["DIA"].strip()== 'VI' and '4',
        }
        pricelist_id = get_pricelist(Ruta["PRECIO"],sucursal)
        pricelist_id and attendance.update({'pricelist_id':pricelist_id})
        attendance_ids.append((0,0,attendance))

# por ultimo el rezagado
if plan_id and attendance_ids:
    object_proxy.execute(DB,uid,PASS,'sale.plan','write',plan_id,{'attendance_ids': attendance_ids})
    print  "se ha editado %s " % object_proxy.execute(DB,uid,PASS,'sale.plan','read',plan_id,['name'])
    
# actualizamos usuario y supervisor en el plan
print 'Asignando usuarios a planificaciones...'
plan_ids = object_proxy.execute(DB,uid,PASS,'sale.plan','search',[('active','=',True)])
for plan in object_proxy.execute(DB,uid,PASS,'sale.plan','read',plan_ids,['name','code','shop_id']):
    suc = object_proxy.execute(DB,uid,PASS,'sale.shop','read',plan['shop_id'][0],['code'])['code']
    cod = plan['code']
    i = suc.lower()+cod.zfill(2)
    d = {}
    if i in vendedores:
        d.update({'user_id':vendedores[i]})
    if i in supervisores:
        d.update({'manager':supervisores[i]})
    if i in tipos:
        categ_id = object_proxy.execute(DB,uid,PASS,'sale.plan.categ','search',[('code','=',tipos[i])])
        categ_id and d.update({'categ_id':categ_id[0]})
    if d:
        object_proxy.execute(DB,uid,PASS,'sale.plan','write',plan['id'],d)
        print  "Se ha actualizado vendedor/supervisor en el plan %s " % plan['name']

