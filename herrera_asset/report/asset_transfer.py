# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_transfer(report_sxw.rml_parse):

    _name = 'report.asset.transfer'

    def __init__(self,cr,uid,name,context=None):
        
        super(asset_transfer,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_process_transfer':self._process_transfer,
            'time':time,
            })
        self.context = context
    
    
    def _process_transfer(self,o,data):
        
        asset_obj = self.pool.get('account.asset.asset')
        category_obj = self.pool.get ('account.asset.category')
        objects = asset_obj.browse(self.cr,self.uid, data['asset_ids'])
        
        vals = []
        assets = {}
        fields= {'shop_id': data['shop_id'][0]}

        for line in objects:
            if data['department_id']:
                fields.update({'department_id': data['department_id'][0]})
            if data['employee_id']:
                fields.update({'employee_id': data['employee_id'][0]})
            if data['shop_id']:
                idcat = category_obj.search(self.cr, self.uid, [('shop_id', '=', data['shop_id'][0]),('reference','=', line.category_id.reference)])
                if not idcat:
                    raise osv.except_osv(('Error!'), ("No existe categoria definida que coincida con la categoria del activo '%s', para la sucursal a la que realiza el translado. Contacte con el administrador.!")% (line.code,))
                fields.update({'shop_id': data['shop_id'][0], 'category_id': idcat[0]})
            asset_obj.write(self.cr, self.uid,[line.id],fields)

            assets = {'name_aseet': line.name,'codigo': line.code, 'category': line.category_id.name }
            vals.append(assets)

        return vals

report_sxw.report_sxw('report.asset.transfer', 
                      'account.asset.report', 
                       rml='herrera/herrera_asset/report/transfer_note_report.rml',
                       parser=asset_transfer, 
                       header=False)
