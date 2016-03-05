# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_incidence_rpon(report_sxw.rml_parse):

    _name = 'report.asset.incidence.rpon'

    def __init__(self,cr,uid,name,context=None):
        st = cr.execute ("select state from account_asset_inventory where id = %d "%context.get('active_id'))
        st = cr.fetchall()
        if 'done' in st[0]:
            raise Exception("Este reporte no puede ser generado, debido a que este inventario ya ha sido ajustado .!")
        super(asset_incidence_rpon,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_rpon_found':self._get_rpon_found,
            'get_other_rpon':self._get_other_rpon,
            'get_rpon_without':self._get_rpon_without,
            'time':time,
            })
        self.context = context
    
    
    def _get_rpon_found(self,o,data): #activos que se registraron en el inventario con los mismos responsables q en la base de datos

        for i in o:
            inv_id = i.id

        query = self.cr.execute(''' SELECT employee_id 
                                    FROM asset_inventory_line as line 
                                    WHERE line.wizard_id = %s and EXISTS (SELECT employee_id
                                                     FROM account_asset_asset as asset
                                                     WHERE asset.employee_id = line.employee_id) '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
        
        
    def _get_other_rpon(self,o,data): #activos que en el inventario se registraron con un responsable y en la base de datos tienen otro
        for i in o:
            inv_id = i.id
      
        query = self.cr.execute(''' SELECT employee_id 
                                    FROM asset_inventory_line as line 
                                    WHERE line.wizard_id = %s and NOT EXISTS (SELECT employee_id
                                                     FROM account_asset_asset as asset
                                                     WHERE asset.employee_id = line.employee_id)   '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
    
    def _get_rpon_without(self,o,data): #activos que en la base de datos no tienen responsable y en el inventario si
        for i in o:
            inv_id = i.id
        query = self.cr.execute(''' SELECT asset.id as asset_id, asset.name as name_aseet, asset.code as codigo
                                    FROM account_asset_asset as asset 
                                    WHERE asset.employee_id is NULL and EXISTS (SELECT code 
                                                            FROM asset_inventory_line as line 
                                                            WHERE asset.code = line.code and wizard_id = %s)  '''% (inv_id))
        query = self.cr.dictfetchall() 
        return query   

report_sxw.report_sxw('report.asset.incidence.rpon', 
                      'account.asset.inventory', 
                       rml='herrera/herrera_asset/report/incidence_rpon.rml',
                       parser=asset_incidence_rpon, 
                       header=False )
