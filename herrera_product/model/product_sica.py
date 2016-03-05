# -*- encoding: utf-8 -*-
############################################################################
#    Module Writen to OpenERP, Open Source Management Solution             #
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).            #
#    All Rights Reserved                                                   #
###############Credits######################################################

############################################################################

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class product_sica(osv.osv):
    
    """
    Product SICA information. For more details visit: https://sistema.sada.gob.ve/print_report_rubros.php
    """
    
    _name = 'product.sica'
    
    _columns = {
            'name':fields.char('Rubro', 100, required = True, help='Official Name SICA'), 
            'code':fields.char('Codigo', 4, required = True, help='Code number SICA'), 
            'pr':fields.boolean('Regulado', help='Code number SICA'),
            'abrv':fields.char('Abrev.', 10, help='Offical Abreviature SICA'),
            'description':fields.text('Items que Aplica', help='Code number SICA'), 
            }

product_sica()
