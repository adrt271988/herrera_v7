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

class account_balance_general_report(osv.osv_memory):
    _name = "account.balance.general.report"
    _description = "Balance de Comprobacion"


    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Plan de Cuentas', help='Seleccione Plan de Cuentas', required=True, domain = [('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio Fiscal', help='Mantenga vacío para todo el año fiscal abierto'),
        'period_from': fields.many2one('account.period', 'Periodo Desde'),
        'period_to': fields.many2one('account.period', 'Periodo Hasta'),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'account_from': fields.many2one('account.account','Cuenta Desde'),
        'account_to': fields.many2one('account.account','Cuenta Hasta'),
        'date': fields.date('Fecha Hasta'),
        'period': fields.many2one('account.period', 'Periodo'),
        'level_in': fields.integer('Nivel',size=1),
        'type': fields.selection([('detail', 'Detallado'), 
                                  ('summary', 'Resumido'), 
                                  ('selection', 'Por Selección')], "Tipo", required=True),
        'filter': fields.selection([('filter_no', 'Sin Filtro'), 
                                    ('filter_date', 'Por Fecha'), 
                                    ('filter_period', 'Por Periodo')], "Filtrado por", required=True),
        }

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {'value': {}}
        cr.execute('''SELECT min(p.date_start)
                          FROM account_period p
                          JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                          WHERE f.id = %d '''%fiscalyear_id)
        date_from =  [i[0] for i in cr.fetchall()][0]
            
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': date_from ,'date_to': False}
        
        if filter == 'filter_date':
            cr.execute('''SELECT min(p.date_start)         
                          FROM account_period p
                          JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                          WHERE f.id = %d '''%fiscalyear_id)
            date_from =  [i[0] for i in cr.fetchall()][0]

            res['value'] = {'period_from': False, 'period_to': False, 'date_from': date_from, 'date_to': time.strftime('%Y-%m-%d')}
        
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.special = false
                               ORDER BY p.date_start ASC, p.special ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods =  [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res


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
            'filter': 'filter_no',
            'chart_account_id': _get_account,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'period': _get_period,

    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from', 'date_to', 'fiscalyear_id','period_from','period_to','account_from','account_to','filter','type','level_in', 'chart_account_id','date','period'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id', 'period_from','period_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        
        if data['form']['type'] == 'selection':
            code_fr = self.pool.get('account.account').read(cr, uid, data['form']['account_from'][0], ['code'], context=context)
            code_to = self.pool.get('account.account').read(cr, uid, data['form']['account_to'][0], ['code'], context=context)
            data['form']['account_from'] = code_fr['code']
            data['form']['account_to'] = code_to['code']
        return{
                'type':'ir.actions.report.xml',   #Tipo de accion que se va a ejecutar
                'report_name': 'general.balance',   #Nombre que se se definio en el .xml de report
                'datas':data,  #Se muestra los datos en la variable
              }
account_balance_general_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
