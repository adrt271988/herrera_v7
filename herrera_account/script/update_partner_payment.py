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
HOST='localhost'
PORT=8069
DB='bd1'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)
common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
#~ 363
#~ 585
#~ 592

###Me logueo
uid = common_proxy.login(DB,USER,PASS)

condition_default = object_proxy.execute(DB,uid,PASS,'account.payment.condition','search',[('code','=','1')]) or False
condition_default = condition_default and condition_default[0]
condition_ids = object_proxy.execute(DB,uid,PASS,'account.payment.condition','search',[('active','=',True)])
condition_all = object_proxy.execute(DB,uid,PASS,'account.payment.condition','read', condition_ids, [])
terms_default = {}
for c in condition_all:
    terms_default.update({c['id']:c['payment_term'][0]})
fields = ['name','payment_condition','supplier_payment_condition','property_supplier_payment_term','property_payment_term']
partner_ids = object_proxy.execute(DB,uid,PASS,'res.partner','search',[('active','=',True),('customer','=',True)])
#~ partner_all = object_proxy.execute(DB,uid,PASS,'res.partner','read',partner_ids,fields)
i = 1
for partner_id in partner_ids:
    partner = object_proxy.execute(DB,uid,PASS,'res.partner','read',partner_id,fields)
    condition = partner['payment_condition']
    condition_id = condition and condition[0]
    if not condition_id:
        condition_id = condition_default
    p = {
        'payment_condition':condition_id,
        'supplier_payment_condition':condition_id,
        'property_supplier_payment_term':terms_default[condition_id],
        'property_payment_term':terms_default[condition_id],
    }
    object_proxy.execute(DB,uid,PASS,'res.partner','write',partner_id, p)
    print '%s: Actualizado cliente %s'%(i,partner['name'])
    i += 1
     
