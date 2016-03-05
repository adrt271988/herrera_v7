# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class inherited_partner(osv.osv):
    """
    Herrera Customizations for res.partner model
    """
    _inherit = "res.partner"

    def _get_comercials(self, cr, uid, ids, field_name, args, context=None):
        """ Create a dictionary with ids pickings and their browse item 
        """
        context = context or {}
        res = {}
        plan_obj = self.pool.get('sale.plan')
        attendance_obj = self.pool.get('sale.plan.attendance')
        for b in self.browse(cr, uid, ids, context=context):
            res[b.id] = [1]
            for a in attendance_obj.search(cr, uid, [('partner_id','=',b.id)], context=context):
                attendance_brw = attendance_obj.browse(cr, uid, a, context=context)
                res[b.id].extend(attendance_brw.plan_id.user_id and [attendance_brw.plan_id.user_id.id] or [])
        return res
        
    _columns = {
        'comercial_list' : fields.function(_get_comercials, type='char', string='Vendedores', store=False, method=False, help='Listado de vendedores que pueden visitar a este cliente'),
    }
    
    #~ _defaults = {
    #~ }

inherited_partner()


