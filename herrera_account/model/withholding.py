# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import calendar
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import openerp.addons.decimal_precision as dp


class taxes_withholding(osv.osv):

    _name = 'taxes.withholding'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: 
            context = {}
        res = super(taxes_withholding, self).default_get(cr, uid, fields, context=context)
        if context.get('withholding_islr',False):
            res.update({'type': context['withholding_islr'] })
        elif context.get('withholding_iva', False):
            res.update({'type': context['withholding_iva'] })
            
        return res 
         
    _columns = {
                 'name': fields.char('Nombre', size=25, required= True),
                 'code': fields.char('Código', size=5, required= True),
                 'percent': fields.float('Porcentaje (%)', digits_compute=dp.get_precision('Account'), required=True),
                 'deductible' : fields.float('Deducible',  digits_compute=dp.get_precision('Account'), required=True),
                 'top': fields.float('Tope',  digits_compute=dp.get_precision('Account'), required=True),
                 'type': fields.selection([('iva', 'IVA'),('islr', 'ISLR')], 'Tipo de retención',required=True)
                }

taxes_withholding()
