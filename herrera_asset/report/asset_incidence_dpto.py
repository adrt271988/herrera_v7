# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_incidence_dpto(report_sxw.rml_parse):

    _name = 'report.asset.incidence.dpto'

    def __init__(self,cr,uid,name,context=None):
        st = cr.execute ("select state from account_asset_inventory where id = %d "%context.get('active_id'))
        st = cr.fetchall()
        if 'done' in st[0]:
            raise Exception("Este reporte no puede ser generado, debido a que este inventario ya ha sido ajustado .!")
        super(asset_incidence_dpto,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_dpto_found':self._get_dpto_found,
            'get_dpto_no_found':self._get_dpto_no_found,
            'get_other_dpto':self._get_other_dpto,
            'get_dpto_without':self._get_dpto_without,
            'time':time,
            })
        self.context = context
    
    
    def _get_dpto_found(self,o,data):

        for i in o:
            inv_id = i.id
      
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, dpto.name as departamento, empl.name_related as empleado
                                    FROM account_asset_inventory as inv
                                    JOIN asset_inventory_line line on inv.id = line.wizard_id
                                    JOIN account_asset_asset as asset on asset.id = line.asset_id
                                    JOIN hr_employee empl on empl.id = line.employee_id
                                    JOIN hr_department dpto on dpto.id=asset.department_id
                                    WHERE line.wizard_id = %s and asset.state = 'open' and line.department_id = inv.department_id  '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
        
    def _get_dpto_no_found(self,o,data):
        for i in o:
            inv_id = i.id
            inv_dpto = i.department_id.id
        query = self.cr.execute(''' SELECT asset.id as asset_id, asset.name as name_aseet, asset.code as codigo, dpto.name as departamento,empl.name_related as empleado
                                    FROM account_asset_asset as asset 
                                    JOIN hr_employee empl on empl.id = asset.employee_id
                                    JOIN hr_department dpto on dpto.id=asset.department_id
                                    WHERE asset.department_id = %s and asset.state = 'open' and NOT EXISTS (SELECT code FROM asset_inventory_line as line WHERE asset.code = line.code and wizard_id = %s)   '''% (inv_dpto,inv_id))
        query = self.cr.dictfetchall() 
        return query
        
    def _get_other_dpto(self,o,data):
        for i in o:
            inv_id = i.id
      
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, dpto.name as departamento, empl.name_related as empleado
                                    FROM account_asset_inventory as inv
                                    JOIN asset_inventory_line line on inv.id = line.wizard_id
                                    JOIN account_asset_asset as asset on asset.id = line.asset_id
                                    JOIN hr_employee empl on empl.id = line.employee_id
                                    JOIN hr_department dpto on dpto.id=asset.department_id
                                    WHERE line.wizard_id = %s and asset.state = 'open' and line.department_id != inv.department_id  '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
    
    def _get_dpto_without(self,o,data):
        for i in o:
            inv_id = i.id
        query = self.cr.execute(''' SELECT asset.id as asset_id, asset.name as name_aseet, asset.code as codigo, empl.name_related as empleado
                                    FROM account_asset_asset as asset 
                                    JOIN hr_employee empl on empl.id = asset.employee_id
                                    WHERE asset.department_id is NULL and asset.state = 'open' and EXISTS (SELECT code FROM asset_inventory_line as line WHERE asset.code = line.code and wizard_id = %s)  '''% (inv_id))
        query = self.cr.dictfetchall() 
        return query   

report_sxw.report_sxw('report.asset.incidence.dpto', 
                      'account.asset.inventory', 
                       rml='herrera/herrera_asset/report/incidence_dpto.rml',
                       parser=asset_incidence_dpto, 
                       header=False )
