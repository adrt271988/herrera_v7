from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class inherit_res_company(osv.osv):
    
    '''Herencia del modelo res.company '''
    
    _inherit = 'res.company'
    
    _columns = {
        'merchandise_insured_amount': fields.float('Monto de Mercancia Flotante Asegurada'),
        'lines_invoice':fields.integer('Invoice Lines',required=False, help="Number of lines per invoice"),
        'max_inv_print':fields.integer('Max. Invoice Prints',required=False, help="Maximum number of prints per invoice"),
    }
                
    
    _defaults = {
        'lines_invoice':7,
        'max_inv_print':1,
    }
inherit_res_company()
