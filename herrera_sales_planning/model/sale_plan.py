# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class sale_plan(osv.osv):
    _name = 'sale.plan'
    _description = "Sale Plan"
    
    def onchange_user(self, cr, uid, ids, user_id, context=None):
        res = {}
        if user_id:
            brw = self.pool.get('res.users').browse(cr, uid, user_id, context=context)
            res.update({'value': {'shop_id': brw.shop_id.id } })
        return res

    def switch_to_weekly(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return super(sale_plan,self).write(cr, uid, ids, {'frequency':'weekly'}, context=context)
        
    def switch_to_monthly(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return super(sale_plan,self).write(cr, uid, ids, {'frequency':'monthly'}, context=context)
        
    def auth_active(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        plan = self.browse(cr, uid, ids[0], context=context)
        request_obj = self.pool.get('mail.authorization.request')
        auth_id = False
        result = False
        name = plan.name
        active = plan.active
        if active:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_sale_plan_unset_active')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        else:
            obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_sale_plan_set_active')])
            auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
        if auth_id:
            request_obj.create(cr, uid, {
                    'name': 'Solicitud para modificación de Planificación de Venta',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': plan.id,
            })
        return result
        
    _columns = {
        'name' : fields.char("Name", size=64, required=True),
        'code' : fields.char("Code", size=2, required=True),
        'manager' : fields.many2one('res.users', 'Manager'),
        'is_manager' : fields.boolean('Is manager?'),
        'user_id' : fields.many2one('res.users', 'Salesman'),
        'attendance_ids' : fields.one2many('sale.plan.attendance', 'plan_id', 'Customers'),
        'frequency': fields.selection([('weekly','Semanal'),('biweekly','Quincenal'),('monthly','Mensual')], 'Frequency'),
        'product_ids':fields.many2many('product.product', 'product_salesman_rel', 'product_id', 'user_id', 'Products handled'),
        'categ_id': fields.many2one('sale.plan.categ', 'Category'),
        'shop_id': fields.many2one('sale.shop', 'Sucursal', required=True),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': True,
        'frequency': 'weekly',
    }
        
sale_plan()

class sale_plan_attendance(osv.osv):
    _name = 'sale.plan.attendance'
    _description = "Sale Plan Detail"
    _order = 'dayofweek'
    _columns = {
        'name' : fields.char("Name", size=64, required=True),
        'dayofweek': fields.selection([('0','Lunes'),('1','Martes'),('2','Miercoles'),('3','Jueves'),('4','Viernes'),('5','Sabado'),('6','Domingo')], 'Day of Week', select=True),
        'plan_id' : fields.many2one("sale.plan", "Sale Plan", required=True, ondelete='cascade'),
        'pricelist_id': fields.many2one('product.pricelist', 'Tarifa', domain="[('type','=','sale')]"),
        'partner_id' : fields.many2one("res.partner", "Cliente"),
        'boletin': fields.boolean('Aplica Boletín', help="Campo para definir si para esta planificación posee descuentos u ofertas"),
    }

sale_plan_attendance()

class sale_plan_categ(osv.osv):
    _name = 'sale.plan.categ'
    _description = "Salesman Category"

    _columns = {
        'name': fields.char('Tipo', help="Tipo de Vendedor"),
        'code': fields.char('Código', size = 1),
    }

sale_plan_categ()
