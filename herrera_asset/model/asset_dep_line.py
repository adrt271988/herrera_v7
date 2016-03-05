# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import openerp.addons.decimal_precision as dp


class inherited_depreciation_line(osv.osv):


    _inherit = 'account.asset.depreciation.line'

    def create_move(self, cr, uid, ids, context=None): # herencia del metodo "create_move". boton : "crear asiento"
        
        asset_obj = self.pool.get('account.asset.asset')
        currency_obj = self.pool.get('res.currency')
        account_move_id = super(inherited_depreciation_line, self).create_move(cr, uid, ids, context=context)
        depreci_line_id = self.search(cr, uid, [('move_id', '=', account_move_id)], context=context)
        seat = self.browse(cr, uid, depreci_line_id[0], context=context)

        if seat:
            asset = asset_obj.browse(cr, uid, seat.asset_id.id, context=context)
            asset_obj.write(cr, uid, [seat.asset_id.id], {'value_current': asset.value_residual }, context=context)
 
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'open'})    
        return account_move_id

    _columns = {}

inherited_depreciation_line()
