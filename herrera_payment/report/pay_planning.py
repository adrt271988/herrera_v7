# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class pay_planning(report_sxw.rml_parse):
    _name = 'report.pay.planning'

    def __init__(self,cr,uid,name,context=None):

        super(pay_planning,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_all_list':self._get_all_list,
            'time':time,
            })
        self.context = context


    def _get_all_list(self,o,data):
        
        fecha_inicial = datetime.strptime(data['date_from'], "%Y-%m-%d")
        fecha_final = datetime.strptime(data['date_until'], "%Y-%m-%d")
        dif = (fecha_final - fecha_inicial).days
        reg = []
        total_col = 0
        partners = self.cr.execute('''  SELECT rp.id as prov_id
                                        FROM account_invoice as inv
                                        JOIN res_partner rp on rp.id = inv.partner_id 
                                        WHERE inv.date_due between  '%s' and '%s' and inv.type = 'in_invoice' and (inv.state = 'open' or inv.state = 'draft')
                                        GROUP BY rp.id'''%(data['date_from'],data['date_until']))
        partners = self.cr.dictfetchall()

        for i in partners:
            
            line = self.cr.execute('''  SELECT rp.name, rp.id as prov_id, inv.date_due as venc, sum(inv.residual) as monto
                                        FROM account_invoice as inv
                                        JOIN res_partner rp on rp.id = inv.partner_id 
                                        WHERE rp.id = %d and inv.date_due between '%s' and '%s' and inv.type = 'in_invoice' and (inv.state = 'open' or inv.state = 'draft')
                                        GROUP BY rp.id,rp.name,inv.date_due'''%(i['prov_id'],data['date_from'],data['date_until']))
            line = self.cr.dictfetchall()
            vals = {}
            total_row = 0

            for j in line:
                k = j.values()
                vals.update({'id': k[0],'monto_'+str(k[3]):k[1], 'name':k[2] , 'fecha_'+str(k[3]): k[3] })
                total_row += k[1]
            total_col += total_row
            vals.update({'total_row': total_row })
            reg.append(vals)
        
        total = {}
        t_1 = t_2 = t_3 = t_4 = t_5 = t_6 = t_7 = 0
        for val in reg:
            t_1 += val.get('monto_'+data['fecha_1'][0:10],0.00)
            t_2 += val.get('monto_'+data['fecha_2'][0:10],0.00)
            t_3 += val.get('monto_'+data['fecha_3'][0:10],0.00)
            t_4 += val.get('monto_'+data['fecha_4'][0:10],0.00)
            t_5 += val.get('monto_'+data['fecha_5'][0:10],0.00)
            t_6 += val.get('monto_'+data['fecha_6'][0:10],0.00)
            t_7 += val.get('monto_'+data['fecha_7'][0:10],0.00)
        total.update({
                    'total_'+data['fecha_1'][0:10]:t_1,
                    'total_'+data['fecha_2'][0:10]:t_2,
                    'total_'+data['fecha_3'][0:10]:t_3,
                    'total_'+data['fecha_4'][0:10]:t_4,
                    'total_'+data['fecha_5'][0:10]:t_5,
                    'total_'+data['fecha_6'][0:10]:t_6,
                    'total_'+data['fecha_7'][0:10]:t_7,
                    'total_col':total_col, 'id': False
                    })
        reg.append(total)
        return reg
    
report_sxw.report_sxw('report.pay.planning',
                      'pay.planning.process',
                       rml='herrera/herrera_payment/report/pay_planning.rml',
                       parser=pay_planning,
                       header=False )

