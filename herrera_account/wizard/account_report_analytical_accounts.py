# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from lxml import etree

from openerp.osv import fields, osv
from openerp.osv.orm import setup_modifiers
from openerp.tools.translate import _

class account_analytical_accounts_report(osv.osv_memory):
    _name = "account.analytical.accounts.report"
    _description = "Analitico de Cuentas"


    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Plan de Cuentas', help='Seleccione Plan de Cuentas', required=True, domain = [('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio Fiscal', help='Mantenga vacío para todo el año fiscal abierto'),
        'account_id': fields.many2one('account.account', 'Cuenta',required= True),
        'account_to': fields.many2one('account.account', 'Cuenta hasta'),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'date': fields.date('Fecha'),
        'period': fields.many2one('account.period', 'Periodo'),
        'type': fields.selection([('single', 'Una Cuenta'), 
                                  ('range', 'Rango de Cuentas')], "Tipo", required=True),
        }

    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
    
    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False


    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'company_id': 1,
            'chart_account_id': _get_account,
            'date_from': time.strftime('%Y-%m-01'),
            'date_to': time.strftime('%Y-%m-%d'),
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'period': _get_period,
             }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from', 'date_to', 'fiscalyear_id','chart_account_id','date','type','period','account_id','account_to'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]

        return{
                'type':'ir.actions.report.xml',   #Tipo de accion que se va a ejecutar
                'report_name': 'analytical.accounts',   #Nombre que se se definio en el .xml de report
                'datas':data,  #Se muestra los datos en la variable
              }
              
account_analytical_accounts_report()
