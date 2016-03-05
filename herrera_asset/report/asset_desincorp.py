# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_desincorporated(report_sxw.rml_parse):

    _name = 'report.asset.desincorporated'

    def __init__(self,cr,uid,name,context=None):
        
        super(asset_desincorporated,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_process_desincorporated':self._process_desincorporated,
            'get_process_amount_desincorporated':self._process_amount_desincorporated,
            'time':time,
            })
        self.context = context
    
    
    def _process_desincorporated(self,o,data):
        query = self.cr.execute(''' SELECT asset.name as name_aseet, asset.code as codigo, categ.name as category, asset.purchase_value as p_compra, asset.date_disincorporate as fecha, asset.value_current as v_actual
                                    FROM account_asset_asset as asset
                                    JOIN account_asset_category categ on asset.category_id = categ.id
                                    WHERE asset.date_disincorporate between '%s' and '%s' and asset.state = 'close'   '''% (data['date_from'],data['date_until']))
        query = self.cr.dictfetchall() 
        return query
        
    def _process_amount_desincorporated(self,o,data):
        query = self.cr.execute(''' SELECT sum(asset.purchase_value) as total_compra, sum(asset.value_current) as total_valor
                                    FROM account_asset_asset as asset
                                    JOIN account_asset_category categ on asset.category_id = categ.id
                                    WHERE asset.date_disincorporate between '%s' and '%s' and asset.state = 'close'   '''% (data['date_from'],data['date_until']))
        query = self.cr.dictfetchall() 
        return query

report_sxw.report_sxw('report.asset.desincorporated', 
                      'account.asset.asset', 
                       rml='herrera/herrera_asset/report/list_desincorp.rml',
                       parser=asset_desincorporated, 
                       header=False )
