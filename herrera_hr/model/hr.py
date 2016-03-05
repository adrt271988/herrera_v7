from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _


class inherited_hr_employee(osv.osv):
    """
    Herrera Customizations for res.partner model
    """
    _inherit = "hr.employee"

    _columns = {
        'shop_id' : fields.many2one("sale.shop", "Sucursal"),
        'entry_date' : fields.date("Fecha de Ingreso", help="Fecha de Ingreso a la Empresa del Trabajador"),
    }
    
inherited_hr_employee()
