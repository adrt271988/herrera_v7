# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class inherited_sale_order(osv.Model):
    _inherit = "sale.order"
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        if context is None: context = {}
        res = super(inherited_sale_order,self).onchange_partner_id(cr, uid, ids, partner_id, context=context)
        attendance_obj = self.pool.get('sale.plan.attendance')
        comercials = []
        for a in attendance_obj.search(cr, uid, [('partner_id','=',partner_id)], context=context):
            attendance_brw = attendance_obj.browse(cr, uid, a, context=context)
            comercials.extend(attendance_brw.plan_id.user_id and [attendance_brw.plan_id.user_id.id] or [])
        if comercials:
            res['value'].update({'user_id': uid in comercials and uid or False })
            res['domain'] = {'user_id': [('id','in',comercials)] }
            
        return res
    
    def onchange_user_id(self, cr, uid, ids, user_id=False, partner_id=False, context = False):
        result = super(inherited_sale_order,self).onchange_user_id(cr, uid, ids, user_id, partner_id, context)
        if user_id and partner_id:
            plan_ids = self.pool.get('sale.plan').search(cr, uid, [('user_id','=',user_id)], context=context)
            if plan_ids:
                line_obj = self.pool.get('sale.plan.attendance')
                line_ids = plan_ids and line_obj.search(cr, uid, [('plan_id','in',plan_ids),('partner_id','=',partner_id)], context=context)
                pricelist_id = line_ids and line_obj.read(cr, uid, line_ids[0], ['pricelist_id'])['pricelist_id']
                if pricelist_id:
                    result.update({'value': {'pricelist_id': pricelist_id}})
        return result
    
    _defaults = {
        'user_id': False,
    }
    
