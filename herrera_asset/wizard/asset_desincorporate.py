

import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class account_asset_desincorporate_process(osv.osv_memory):
    
    _name = 'account.asset.desincorporate.process'
    _columns = { }

    def action_desincorporate(self, cr, uid, ids, context=None):
        can_close = False
        if context is None:
            context = {}
            
        asset_id = context.get('active_ids',[])
        depreciation_date =  datetime.today()
        values = self.read(cr,uid,ids, context=context)
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []

     
        for line in asset_obj.browse(cr, uid, asset_id, context=context):

            ctx = dict(context, account_period_prefer_normal=True)
            period_ids = period_obj.find(cr, uid, depreciation_date, context=ctx)
            company_currency = line.company_id.currency_id.id
            current_currency = line.currency_id.id
            context.update({'date': depreciation_date})
            current_amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.value_residual, context=context)
            purchas_amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.purchase_value, context=context)
            depreci_amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.accumulated_depre, context=context)
           
            sign = (line.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = line.name
            reference = 'Final'
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.category_id.journal_id.id,
                }
            
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.category_id.journal_id.id
            partner_id = line.partner_id.id
            
            if current_amount > 0.00:
                sign = (line.category_id.journal_id.type == 'purchase' and 1) or -1
                move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.category_id.account_desincorporate_id.id,
                'debit': current_amount,
                'credit': 0.0,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * amount or 0.0,
                'analytic_account_id': line.category_id.account_analytic_id.id,
                'date': depreciation_date,
                'asset_id': asset_id[0]
                })
            sign = (line.category_id.journal_id.type == 'purchase' and 1) or -1
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.category_id.account_depreciation_id.id,
                'debit': current_amount > 0.00 and depreci_amount or purchas_amount,
                'credit': 0.00,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * amount or 0.0,
                'date': depreciation_date,
                 })
            
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.category_id.account_asset_id.id,
                'debit': 0.00,
                'credit': purchas_amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * amount or 0.0,
                'date': depreciation_date,
                 })

        asset_obj.write(cr, uid, asset_id, {'state': 'close','date_disincorporate': depreciation_date }, context=context)
        return True

account_asset_desincorporate_process()
