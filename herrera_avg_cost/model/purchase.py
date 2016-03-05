# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class inherited_purchase_order(osv.Model):
    _inherit = "purchase.order"
