# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler


class asset_list(report_sxw.rml_parse):

    _name = 'report.asset.list'

    def __init__(self,cr,uid,name,context=None):

        super(asset_list,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_all_list':self._get_all_list,
            'get_all_list_sum':self._get_all_list_sum,
            'get_type':self._get_type,
            'time':time,
            })
        self.context = context

    def _get_type(self,o,data):
        lista = []
        dicci = {}
        for val in o:
            seleccion = val.select_categ and val.select_categ or val.select_shop and val.select_shop or val.select_parent and val.select_parent
            dicci.update({'grupo': val.report_group, 'seleccion': seleccion })
            lista.append(dicci)
        return lista

    def _get_all_list(self,o,data):
        lista = []
        for i in o:
            if i.report_group == 'C':
                if i.select_categ == '1': # Una Categoria
                    query = self.cr.execute(''' SELECT asset.name as name, asset.code as codigo, categ.name as category, asset.purchase_value as p_compra, asset.date_incorporation as fecha, asset.value_current as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN account_asset_category categ on asset.category_id = categ.id
                                                WHERE asset.state = 'open' and asset.category_id = %s and asset.code is not null and asset.date_incorporation <= '%s' '''%(i.category_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                    

                else: # Todas las categorias
                
                    cat = self.cr.execute('SELECT reference FROM account_asset_category GROUP BY reference ORDER BY reference ')
                    cat = self.cr.dictfetchall()
                    for lines in cat:
                        line = self.cr.execute(''' SELECT categ.name as name, categ.reference as codigo, sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                    FROM account_asset_asset as asset
                                                    RIGHT JOIN account_asset_category categ on asset.category_id = categ.id
                                                    WHERE asset.state = 'open' and categ.reference = '%s' and asset.date_incorporation <= '%s'
                                                    GROUP BY categ.name,categ.reference
                                                    ORDER BY categ.name,categ.reference
                                                     '''%(lines['reference'],data['date_stop']))
                        line = self.cr.dictfetchall()

                        total = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                    FROM account_asset_asset as asset
                                                    JOIN account_asset_category categ on asset.category_id = categ.id
                                                    WHERE asset.state = 'open' and categ.reference = '%s' and asset.date_incorporation <= '%s' 
                                                    '''%(lines['reference'],data['date_stop']))
                        total = self.cr.dictfetchall()
                        total[0].update({'name':'*** Sub-Total Categoria %s ***'%lines['reference'],'codigo':'**'})
                        line.append(total[0])
                        lista.extend(line) #extend une las listas en una lista existente
                    query = lista

            if i.report_group == 'S':

                if i.select_shop == '1':
                    query = self.cr.execute(''' SELECT asset.name as name, asset.code as codigo, shop.name as sucursal, asset.purchase_value as p_compra, asset.date_incorporation as fecha, asset.value_current as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN sale_shop shop on asset.shop_id = shop.id
                                                WHERE asset.state = 'open' and asset.shop_id = %s and asset.date_incorporation <= '%s' 
                                                '''%(i.shop_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                else:
                    query = self.cr.execute(''' SELECT shop.name as name, sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual,shop.code as codigo
                                                FROM account_asset_asset as asset
                                                RIGHT JOIN sale_shop shop on asset.shop_id = shop.id
                                                WHERE asset.state = 'open' and asset.date_incorporation <= '%s'
                                                GROUP BY shop.name,shop.code
                                                ORDER BY shop.name,shop.code '''%data['date_stop'])
                    query = self.cr.dictfetchall()

            if i.report_group == 'P':
                if i.select_parent == '1':
                    query = self.cr.execute(''' SELECT asset.name as name, asset.code as codigo, asset.purchase_value as p_compra, asset.date_incorporation as fecha, asset.value_current as v_actual
                                                FROM account_asset_asset as asset
                                                WHERE asset.state = 'open' and asset.parent_id is Null and asset_id = %s and asset.code is not null and asset.date_incorporation <= '%s' 
                                                '''%(i.asset_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                else:
                    query = self.cr.execute(''' SELECT asset.name as name, asset.code as codigo, asset.purchase_value as p_compra, asset.date_incorporation as fecha, asset.value_current as v_actual
                                                FROM account_asset_asset as asset
                                                WHERE asset.state = 'open' and asset.parent_id is Null and asset.code is not null and asset.date_incorporation <= '%s'
                                                GROUP BY asset.name,asset.code,asset.purchase_value,asset.date_incorporation,asset.value_current,asset.id
                                                ORDER BY asset.id '''%data['date_stop'])
                    query = self.cr.dictfetchall()

        return query
    
    ################## TOTALES ############################
    
    def _get_all_list_sum(self,o,data):

        for i in o:

            if i.report_group == 'C':
                if i.select_categ == '1':
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN account_asset_category categ on asset.category_id = categ.id
                                                WHERE asset.category_id = %s and asset.date_incorporation <= '%s'  
                                                '''%(i.category_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                else:
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN account_asset_category categ on asset.category_id = categ.id
                                                WHERE asset.state = 'open' and asset.date_incorporation <= '%s' 
                                                '''%data['date_stop'])
                    query = self.cr.dictfetchall()



            if i.report_group == 'S':

                if i.select_shop == '1':
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN sale_shop shop on asset.shop_id = shop.id
                                                WHERE asset.shop_id = %s and asset.date_incorporation <= '%s' 
                                                '''%(i.shop_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                else:
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                JOIN sale_shop shop on asset.shop_id = shop.id
                                                WHERE asset.state = 'open' and asset.date_incorporation <= '%s' 
                                                '''%data['date_stop'])
                    query = self.cr.dictfetchall()

            if i.report_group == 'P':
                if i.select_parent == '1':
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                WHERE asset.parent_id is Null  and asset_id = %s and asset.date_incorporation <= '%s'  
                                                '''%(i.asset_id.id,data['date_stop']))
                    query = self.cr.dictfetchall()
                else:
                    query = self.cr.execute(''' SELECT sum(asset.purchase_value) as p_compra, sum(asset.value_current) as v_actual
                                                FROM account_asset_asset as asset
                                                WHERE asset.state = 'open' and asset.parent_id is Null and asset.date_incorporation <= '%s' 
                                                '''%data['date_stop'])
                    query = self.cr.dictfetchall()

        return query


report_sxw.report_sxw('report.asset.list',
                      'account.asset.report',
                       rml='herrera/herrera_asset/report/asset_list.rml',
                       parser=asset_list,
                       header=False )

