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
uid = common_proxy.login(DB,USER,PASS)
j_model = 'account.journal'
a_model = 'account.account'
journal_ids = object_proxy.execute(DB,uid,PASS,j_model,'search',[('type','in',['bank','cash','iva_sale','islr_sale','mun_sale','sale_dpp','dpp_recovery'])])
journals = object_proxy.execute(DB,uid,PASS,j_model,'read', journal_ids, ['name','type'])
for journal in journals:
    if journal['type'] in ('bank','cash'):
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','11104000')])[0]
    if journal['type'] == 'iva_sale':
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','18101004')])[0]
    if journal['type'] == 'islr_sale':
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','18103006')])[0]
    if journal['type'] == 'mun_sale':
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','18101088')])[0]
    if journal['type'] == 'sale_dpp':
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','42001000')])[0]
    if journal['type'] == 'iva_recovery':
	account_id = object_proxy.execute(DB,uid,PASS,a_model,'search',[('code','=','40001010')])[0]
    object_proxy.execute(DB,uid,PASS,j_model,'write',[journal['id']],{'default_credit_account_id': account_id, 'default_debit_account_id': account_id})
