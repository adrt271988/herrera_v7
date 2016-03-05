# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler
from openerp.tools.translate import _

class asset_incidence_shop(report_sxw.rml_parse):

    _name = 'report.asset.incidence.shop'
    
    #return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name
    def __init__(self,cr,uid,name,context=None):

        #~ st = cr.execute ("select state from account_asset_inventory where id = %d "%context.get('active_id'))
        #~ st = cr.fetchall()
        #~ if 'done' in st[0]:
            #~ raise Exception("Este reporte no puede ser generado, debido a que este inventario ya ha sido ajustado .!") 
        
        super(asset_incidence_shop,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_shop_found':self._get_shop_found,
            'get_shop_no_found':self._get_shop_no_found,
            'get_other_shop':self._get_other_shop,
            'get_shop_without':self._get_shop_without,
            'time':time,
            })
        self.context = context

    
    def _get_shop_found(self,o,data):
        
        for i in o:
            inv_id = i.id
      
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, sh.code as sucursal, empl.name_related as empleado, asset.purchase_value as p_compra, asset.value_current as v_actual
                                    FROM account_asset_inventory as inv
                                    JOIN asset_inventory_line line on inv.id = line.wizard_id
                                    JOIN account_asset_asset as asset on asset.id = line.asset_id
                                    LEFT JOIN hr_employee empl on empl.id = line.employee_id
                                    JOIN sale_shop sh on sh.id=asset.shop_id
                                    WHERE line.wizard_id = %s and line.shop_id = inv.shop_id and asset.state = 'open' '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
        
    def _get_shop_no_found(self,o,data):
        for i in o:
            inv_id = i.id
            inv_shop = i.shop_id.id
        query = self.cr.execute(''' SELECT asset.id as asset_id, asset.name as name_aseet, asset.code as codigo, sh.code as sucursal,empl.name_related as empleado, asset.purchase_value as p_compra, asset.value_current as v_actual
                                    FROM account_asset_asset as asset 
                                    LEFT JOIN hr_employee empl on empl.id = asset.employee_id
                                    JOIN sale_shop sh on sh.id=asset.shop_id
                                    WHERE asset.shop_id = %s and asset.state = 'open' and NOT EXISTS (SELECT code FROM asset_inventory_line as line WHERE asset.code = line.code and wizard_id = %s)   '''% (inv_shop,inv_id))
        query = self.cr.dictfetchall() 
        return query
        
    def _get_other_shop(self,o,data):
        for i in o:
            inv_id = i.id
      
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, sh.code as sucursal, empl.name_related as empleado, asset.purchase_value as p_compra, asset.value_current as v_actual
                                    FROM account_asset_inventory as inv
                                    JOIN asset_inventory_line line on inv.id = line.wizard_id
                                    JOIN account_asset_asset as asset on asset.id = line.asset_id
                                    LEFT JOIN hr_employee empl on empl.id = line.employee_id
                                    JOIN sale_shop sh on sh.id=asset.shop_id
                                    WHERE line.wizard_id = %s and asset.state = 'open' and line.shop_id != inv.shop_id  '''%inv_id)
        query = self.cr.dictfetchall() 
        return query
    
    def _get_shop_without(self,o,data):
        for i in o:
            inv_id = i.id
        query = self.cr.execute(''' SELECT asset.id as asset_id, asset.name as name_aseet, asset.code as codigo, empl.name_related as empleado, asset.purchase_value as p_compra, asset.value_current as v_actual
                                    FROM account_asset_asset as asset 
                                    LEFT JOIN hr_employee empl on empl.id = asset.employee_id
                                    WHERE asset.shop_id is NULL and asset.state = 'open' and EXISTS (SELECT code FROM asset_inventory_line as line WHERE asset.code = line.code and wizard_id = %s)  '''% (inv_id))
        query = self.cr.dictfetchall() 
        return query   

report_sxw.report_sxw('report.asset.incidence.shop', 
                      'account.asset.inventory', 
                       rml='herrera/herrera_asset/report/incidence_shop.rml',
                       parser=asset_incidence_shop, 
                       header=False )
