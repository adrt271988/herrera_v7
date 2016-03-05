# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools


class inherited_asset_category(osv.osv):
    
    
    _inherit = 'account.asset.category'
    
    _columns = {
                 'policy_number': fields.char('Numero de Poliza', size=20),
                 'account_desincorporate_id': fields.many2one('account.account', 'Cuenta desincorporación', required=True),
                 'shop_id' : fields.many2one('sale.shop', 'Sucursal', required=True),
                 'reference': fields.char('Referencia tipo', required=True, size=3, help="Código de referencia (3 caracteres) para el tipo de categoría, este código debe ser igual para todas las categorias de un mismo tipo."),
                }
             
inherited_asset_category()
