from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools


class inherited_asset(osv.osv):

    _inherit = 'account.asset.asset'

    #~ def write(self, cr, uid, ids, vals, context=None):
        #~ if context is None:
            #~ context = {}
        #~ keys = vals.keys()
        #~ if 'ref' in keys:
            #~ total_amount = 0.00
            #~ for i in vals['cost_ids']:
                #~ for j in i:
                    #~ if type(j) == dict:
                        #~ total_amount += j.get('amount')
            #~ vals['total_amount'] = total_amount
        #~ super(inherited_asset, self).write(cr, uid, ids, vals, context=context)
        #~ return True

inherited_asset()
