# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
import openerp.exceptions
from openerp.osv.orm import except_orm
from openerp.tools.translate import _


class account_invoice_motive(osv.osv):

    _name = "account.invoice.motive"
    _columns = {
            'name': fields.char('Nombre', help="Descripción del motivo"),
            'code': fields.char('Código', size=10, help="Código del motivo"),
    }

account_invoice_motive()
