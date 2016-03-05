# -*- coding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class pay_planning_process(osv.osv_memory):

    _name = 'pay.planning.process'
    _columns = {
                'date_from' :fields.date('Desde', required=True),
                'date_until' :fields.date('Hasta', required=True),
                }
    
    
    def action_generate(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        #date_current = strftime("%A, %d %B de %Y", gmtime())
        
        
        datas={'ids':context.get('active_ids',[])}#la variable (data) almacena los ids activos
        res=self.read(cr,uid,ids, context=context)#la variable (res) almacena las lecturas realizadas
        res=res and res[0] or {}
        datas['form']=res
        
        fecha_inicial = datetime.strptime(res['date_from'], "%Y-%m-%d")
        fecha_final = datetime.strptime(res['date_until'], "%Y-%m-%d")
        dif = (fecha_final - fecha_inicial).days
        if dif > 6 or dif < 1:
            raise osv.except_osv(_('Warning!'), _('Debe seleccionar un rango de fechas no mayor a cinco(7) dias, y la fecha hasta siempre debe ser mayor a la fecha desde.!'))
        fechas = {
                  'fecha_1': fecha_inicial.strftime('%Y-%m-%d %A'), 
                  'fecha_2': (fecha_inicial + timedelta(days=1)).strftime('%Y-%m-%d %A'),
                  'fecha_3': (fecha_inicial + timedelta(days=2)).strftime('%Y-%m-%d %A'),
                  'fecha_4': (fecha_inicial + timedelta(days=3)).strftime('%Y-%m-%d %A'),
                  'fecha_5': (fecha_inicial + timedelta(days=4)).strftime('%Y-%m-%d %A'),
                  'fecha_6': (fecha_inicial + timedelta(days=5)).strftime('%Y-%m-%d %A'),
                  'fecha_7': fecha_final.strftime('%Y-%m-%d %A'),
                 }
        res.update(fechas)
        return{
                'type':'ir.actions.report.xml',   #Tipo de accion que se va a ejecutar
                'report_name': 'pay.planning',   #Nombre que se se definio en el .xml de report
                'datas':res,  #Se muestra los datos en la variable
              }
pay_planning_process()

