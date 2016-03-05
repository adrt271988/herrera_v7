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


class inherit_account_tax(osv.osv):

    _inherit = 'account.tax'
    
    _columns = {
                 'withholding': fields.boolean('Retención', help="Marque este campo si el impuesto es una retención"),
                }

inherit_account_tax()
