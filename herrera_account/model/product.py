# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

import decimal_precision as dp
import pooler
import time
import math

class inherited_product(osv.osv):
    
    '''
        Herencia del modelo product.product para agregar campos 
        inherentes a contabilidad y que son necesarios en Herrera C.A. 
    '''
    
    _inherit = 'product.product'
    
    def _default_property_account_income(self, cr, uid, context=None):
        account_income_id = self.pool.get('account.account').search(cr, uid, [('code','=','40001001')], context=context)
        return account_income_id and account_income_id[0]

    def _default_property_account_expense(self, cr, uid, context=None):
        account_expense_id = self.pool.get('account.account').search(cr, uid, [('code','=','11501001')], context=context)
        return account_expense_id and account_expense_id[0]
    
    def onchange_product_type(self, cr, uid, ids, product_type, context=None):
        inc = product_type == 'product' and self._default_property_account_income or False
        exp = product_type == 'product' and self._default_property_account_expense or False
        return { 'value': { 'property_account_income': inc, 'property_account_expense': exp } }
        
    _defaults = {
        'property_account_income': _default_property_account_income,
        'property_account_expense': _default_property_account_expense,
    }
        
inherited_product()
