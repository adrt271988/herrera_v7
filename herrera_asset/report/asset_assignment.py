# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_assignment(report_sxw.rml_parse):

    _name = 'report.asset.assignment'

    def __init__(self,cr,uid,name,context=None):
        
        super(asset_assignment,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_process_assignment':self._process_assignment,
            'time':time,
            })
        self.context = context
    
    
    def _process_assignment(self,o,data):
        
        asset_obj = self.pool.get('account.asset.asset')
        objects = asset_obj.browse(self.cr,self.uid, data['asset_ids'])
        vals = []
        assets = {}
        fields= {'employee_id': data['employee_id'][0]}
        
        for line in objects:
            if data['department_id']:
                fields.update({'department_id': data['department_id'][0]})
            if data['shop_id']:
                fields.update({'shop_id': data['shop_id'][0]})
            asset_obj.write(self.cr, self.uid,[line.id],fields)

            assets = {'name_aseet': line.name,'codigo': line.code, 'category': line.category_id.name,'cedula': line.employee_id.identification_id }
            vals.append(assets)
        
        #~ query = self.cr.execute(''' SELECT asset.name as name_aseet,asset.code as codigo, categ.name as category, hr_e.identification_id as cedula
                                    #~ FROM account_asset_asset as asset
                                    #~ JOIN account_asset_category categ on asset.category_id = categ.id 
                                    #~ JOIN hr_employee hr_e on asset.employee_id = hr_e.id 
                                    #~ WHERE asset.id = '%s'  '''%data['asset_id'][0])
        #~ query = self.cr.dictfetchall() 

        return vals

report_sxw.report_sxw('report.asset.assignment', 
                      'account.asset.report', 
                       rml='herrera/herrera_asset/report/assig_note_report.rml',
                       parser=asset_assignment, 
                       header=False)
