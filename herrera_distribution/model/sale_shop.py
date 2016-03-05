# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta


class inherited_distribution_sale_shop(osv.osv):
    
    _inherit = 'sale.shop'
    
    _columns = {           
                'address': fields.char(u'Dirección', help="Dirección de la Sucursal"),
                'email': fields.char(u'Correo', help="Correo electrónico de la Sucursal"),
                'phone': fields.char(u'Teléfono', help="Teléfono de contacto de la Sucursal"),
                }
 

inherited_distribution_sale_shop()
