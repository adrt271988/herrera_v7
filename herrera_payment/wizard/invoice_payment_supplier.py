# -*- coding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class invoice_payment_supplier(osv.osv_memory):

    _name = 'invoice.payment.supplier'
    _columns = {

                }
    
    
invoice_payment_supplier()

