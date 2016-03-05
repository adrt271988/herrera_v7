# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta


class inherited_sale_shop(osv.osv):
    
    '''Herencia del modelo sale.shop '''
    
    _inherit = 'sale.shop'
    
    _columns = {           
                'tax_iva': fields.boolean('IVA', help="Marcar si para esta sucursal aplica el impuesto IVA."),
                'code': fields.char('Codigo', size=1, help="Abreviatura de la sucursal (1 solo caracter)"),
                'main': fields.boolean('Principal', help="Sucursal principal de la empresa"),
                }
 

inherited_sale_shop()
