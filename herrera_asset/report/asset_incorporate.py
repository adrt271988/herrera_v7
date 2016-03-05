# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_incorporated(report_sxw.rml_parse):

    _name = 'report.asset.incorporated'

    def __init__(self,cr,uid,name,context=None):
        
        super(asset_incorporated,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_process_incorporated':self._process_incorporated,
            'get_process_amount_incorporated':self._process_amount_incorporated,
            'time':time,
            })
        self.context = context
    
    
    def _process_incorporated(self,o,data):
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, categ.name as category, asset.purchase_value as p_compra, asset.date_incorporation as fecha, asset.value_current as v_actual
                                    FROM account_asset_asset as asset
                                    JOIN account_asset_category categ on asset.category_id = categ.id
                                    WHERE asset.date_incorporation between '%s' and '%s' and asset.state != 'close' and code is not null '''% (data['date_from'],data['date_until']))
        query = self.cr.dictfetchall() 
        return query
        
    def _process_amount_incorporated(self,o,data):
        query = self.cr.execute(''' SELECT sum(asset.purchase_value) as total_compra, sum(asset.value_current) as total_valor
                                    FROM account_asset_asset as asset
                                    JOIN account_asset_category categ on asset.category_id = categ.id
                                    WHERE asset.date_incorporation between '%s' and '%s' and asset.state != 'close' and code is not null  '''% (data['date_from'],data['date_until']))
        query = self.cr.dictfetchall() 
        return query
       

report_sxw.report_sxw('report.asset.incorporated', 
                      'res.users', 
                       rml='herrera/herrera_asset/report/list_incorporate.rml',
                       parser=asset_incorporated, 
                       header=False )
