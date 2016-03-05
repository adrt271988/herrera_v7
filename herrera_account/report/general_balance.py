# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
import datetime
import calendar
from openerp.report import report_sxw
from common_report_header import common_report_header

class general_balance(report_sxw.rml_parse, common_report_header):
    _name = 'report.general.balance'

    def __init__(self, cr, uid, name, context=None):
        super(general_balance, self).__init__(cr, uid, name, context=context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.result_acc = []
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'get_fiscalyear':self._get_fiscalyear,
            'get_filter': self._get_filter,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period ,
            'get_account': self._get_account,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(general_balance, self).set_context(objects, data, new_ids, report_type=report_type)

    def _get_account(self, data):
        if data['model']=='account.account':
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['id']).company_id.name
        return super(general_balance ,self)._get_account(data)

    def lines(self, form, ids=None, done=None):
        
        def _process_child(accounts, parent):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]
               
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                res = {
                    'id': account_rec['id'],
                    'type': account_rec['type'],
                    'code': account_rec['code'],
                    'name': account_rec['name'],
                    'init': account_rec['init'],
                    'level': account_rec['level'],
                    'debit': account_rec['debit'],
                    'credit': account_rec['credit'],
                    'balance': account_rec['balance'],
                    'parent_id': account_rec['parent_id'],
                    'bal_type': '',
                }
                self.sum_debit += account_rec['debit']
                self.sum_credit += account_rec['credit']
                self.result_acc.append(res)
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child(accounts,child)

        obj_account = self.pool.get('account.account')
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}

        #calculo el rango actual de periodos del ejercicio fiscal
        start_period = end_period = False
        self.cr.execute('''    SELECT * FROM (SELECT p.id
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
                               LIMIT 1) AS period_stop''', (form['fiscalyear_id'], form['fiscalyear_id']))
        periods =  [i[0] for i in self.cr.fetchall()]
        if periods and len(periods) > 1:
            start_period = periods[0]
            end_period = periods[1]-1
            if end_period <= start_period:
                start_period = end_period = periods[0]
        else:
            start_period = end_period = periods[0]
            
        ctx = self.context.copy()
        ctxx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctxx['fiscalyear'] = form['fiscalyear_id']
        dia = calendar.monthrange(datetime.datetime.today().year, datetime.datetime.today().month-1)[1] # ultimo dia del mes anterior
        mes = datetime.datetime.today().month-1 # mes anterior
        #print '******form******',form 
        
        #poner la fecha por default tambien si no hay filtros
        
        if form['filter'] == 'filter_period': 
            ctx['period_from'] = form['period_to']
            ctx['period_to'] = form['period_to']
            ctxx['period_from'] = start_period
            ctxx['period_to'] = form['period_to']-1
            #ubi = ctxx['periods'].index(form['period_to']) # agarramos la ubicacion del ultimo periodo 
            #del ctxx['periods'][ubi]
        
        elif form['filter'] == 'filter_date':

            df = datetime.datetime.strptime(form['date_to'],"%Y-%m-%d")
            di = calendar.monthrange(df.year,df.month-1)[1]
            ctx['date_from'] =  time.strftime('%Y-%m-01')
            ctx['date_to'] =  form['date_to']
            ctx['date_from'] =  time.strftime('%Y-'+str(df.strftime('%m'))+'-01')
            
            ctxx['date_from'] =  form['date_from']
            ctxx['date_to'] =  time.strftime('%Y-'+str(int(df.strftime('%m'))-1)+'-'+str(di))
        else:
            ctx['date_from'] =  time.strftime('%Y-%m-01')
            ctx['date_to'] =  time.strftime('%Y-%m-%d')
            
            ctxx['date_from'] =  form['date_from']
            ctxx['date_to'] =  time.strftime('%Y-'+str(mes)+'-'+str(dia))
        
            ctxx['date_from'] =  form['date_from']
            ctxx['date_to'] =  time.strftime('%Y-'+str(mes)+'-'+str(dia))
        #print '************* ctx: para calculo de movimientos actuales **************',ctx
        #print '************* ctxx: para calculo del saldo inicial **************',ctxx
        parents = ids
        child_ids1 = obj_account._get_children_and_consol(self.cr, self.uid, ids, ctx)
        child_ids2 = obj_account._get_children_and_consol(self.cr, self.uid, ids, ctxx)
        if child_ids1 and child_ids2:
            ids1 = child_ids1
            ids2 = child_ids2
 
        #Diccionarios principales
        accounts = obj_account.read(self.cr, self.uid, ids1, ['type','code','name','debit','credit','balance','parent_id','level','child_id'], ctx)
        accounts_two = obj_account.read(self.cr, self.uid, ids2, ['balance'], ctxx) #retorna lista de diccionarios con el saldo inicial
        
        dic_ini = dict(map(lambda x:(x['id'],x['balance']),accounts_two)) #reasignamos llave y valor del diccionario accounts_two
        
        for x in accounts: #actualizamos la lista de diccionarios "accounts" incluyendo el saldo inicial
            i = x['id']
            if i in dic_ini:
                x.update({'init':dic_ini[i]})
        
        for parent in parents:
                if parent in done:
                    continue
                done[parent] = 1
                _process_child(accounts,parent)
        #print self.result_acc
        return self.result_acc

report_sxw.report_sxw('report.general.balance', 
                      'account.account', 
                      'herrera/herrera_account/report/general_balance.rml', 
                      parser=general_balance, header=False)

