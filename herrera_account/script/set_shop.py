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
DB='bd'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)
common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

journal_ids = object_proxy.execute(DB,uid,PASS,'account.journal','search',[])
journal_all = object_proxy.execute(DB,uid,PASS,'account.journal','read', journal_ids, [])
shops = [{'name': 'Barcelona', 'id': 1}, {'name': 'Margarita', 'id': 2}, {'name': 'Cumana', 'id': 3}, {'name': 'Carupano', 'id': 4}, {'name': 'Maturin', 'id': 5}, {'name': 'Maracaibo', 'id': 6}, {'name': 'Punto Fijo', 'id': 7}, {'name': 'Ciudad Bolivar', 'id': 8}, {'name': 'Puerto Ordaz', 'id': 9}, {'name': 'Sede', 'id': 10}]
for shop in shops:
    i = 1
    for journal in journal_all:
	if shop['name'] in journal['name']:
	    object_proxy.execute(DB,uid,PASS,'account.journal','write',journal['id'], {'shop_id': shop['id']})
	    print '%s: Actualizado Diario %s'%(i,journal['name'])
	    i += 1
