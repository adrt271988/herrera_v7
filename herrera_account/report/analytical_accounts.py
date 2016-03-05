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

class analytical_accounts(report_sxw.rml_parse, common_report_header):
    _name = 'report.analytical.accounts'

    def __init__(self, cr, uid, name, context=None):
        super(analytical_accounts, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'get_fiscalyear':self._get_fiscalyear,
            'init_balance': self._init_balance,
             })
        self.context = context

    def _init_balance(self, form, data):

        self.cr.execute(''' SELECT min(date_start)
                            FROM account_period
                            WHERE fiscalyear_id = %s '''%(data['form']['fiscalyear_id']))
        
        date_from = self.cr.dictfetchall()[0]
        
        df = datetime.datetime.strptime(data['form']['date_to'],"%Y-%m-%d")
        mes = df.month-1
        dia = calendar.monthrange(df.year,df.month-1)[1]
        date_to =  time.strftime(str(df.year)+'-'+str(mes)+'-'+str(dia))

        self.cr.execute(''' SELECT COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance
                            FROM account_move_line l
                            WHERE l.account_id = %s and l.date between %s and %s ''', (data['form']['account_id'][0],date_from['min'], date_to))
        
        res = self.cr.dictfetchall()[0]
        return res.get('balance',0.00)
        
    def lines(self, form, data):
        #print '--------------------------',data['form']
        if data['form']['type'] == 'range':
            code_fr = self.pool.get('account.account').read(self.cr, self.uid, data['form']['account_id'][0], ['code'])
            code_to = self.pool.get('account.account').read(self.cr, self.uid, data['form']['account_to'][0], ['code'])
            
            self.cr.execute(''' SELECT a.code as code, c.ref as referencia,c.name as comprobante,l.name as detalle,l.debit as debit ,l.credit as credit
                                FROM account_move c
                                JOIN account_move_line l on c.id = l.move_id
                                JOIN account_account a on a.id = l.account_id
                                WHERE a.code between %s and %s and c.date between %s and %s ''', (code_fr['code'],code_to['code'],data['form']['date_from'], data['form']['date_to']))
            
            res = self.cr.dictfetchall()
        else:
            self.cr.execute(''' SELECT a.code as code,c.ref as referencia,c.name as comprobante,l.name as detalle,l.debit as debit ,l.credit as credit
                                FROM account_move c
                                JOIN account_move_line l on c.id = l.move_id
                                JOIN account_account a on a.id = l.account_id
                                WHERE l.account_id = %s and c.date between %s and %s ''', (data['form']['account_id'][0],data['form']['date_from'], data['form']['date_to']))
            
            res = self.cr.dictfetchall()
        
        for i in res:
            for j in i:
                if type(i[j]) == unicode:
                    i[j]= i[j].strip()
        return res


report_sxw.report_sxw('report.analytical.accounts', 
                      'account.account', 
                      'herrera_account/report/analytical_accounts.rml', 
                       parser=analytical_accounts, header=False)

