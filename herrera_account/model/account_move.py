# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class inherit_account_move(osv.osv):
    
    _inherit = "account.move"
    
    _columns = { 
                'imported': fields.boolean('Importado', help="Indica si el comprobante fue generado a traves de la importacion de datos.") 
               }
    _defaults = {
                'imported': False
                }
    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, ref, date)', 'La combinacion de Numero,Fecha y Referencia interna debe ser unica !'),
    ]
inherit_account_move()

