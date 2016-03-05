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

class sale_budget(osv.osv):
    """ Sales Team Budget """
    _name = 'sale.budget'

    _columns = {
        'name': fields.char('Descripcion', size=64, required=True),
        'plan_id' : fields.many2one("sale.plan", "Responsable", help="Plan de venta realcionado al presupuesto", required=True),
        'fiscalyear_id': fields.many2one("account.fiscalyear", "Ejercicio Fiscal", required=True),
        'period_id': fields.many2one('account.period',"Periodo", required=True),
        'lines_ids' : fields.one2many('sale.line', 'budget_id', 'Presupuestos'),
        'date_begin' : fields.date('Fecha inicio', help="Fecha para la cual empieza a aplicar este presupuesto", required=True),
        'date_end' : fields.date('Fecha fin', help="Fecha de culminación de este presupuesto", required=True),
    }
    #~ 
    #~ def get_domain_user_id(self, cr, uid, ids, context=None):
        #~ res = {}
        #~ member_ids = []
        #~ section_id = self.pool.get('crm.case.section').search(cr, uid, [('user_id','=',uid)])
        #~ if section_id:
            #~ section_brw = self.pool.get('crm.case.section').browse(cr, uid, section_id[0])
            #~ for user in section_brw.member_ids:
                #~ member_ids.append(user.id)
        #~ if not member_ids:
            #~ res.update({'warning':{'title': 'Operación no permitida!','message':"Usted debe tener vendedores a su cargo para poder usar esta opcion, consulte con su administrador de sistema."}})
        #~ res.update({'domain':{'user_id':[('id','in',member_ids)]}})
        #~ return res

sale_budget()

class sale_budget_line(osv.osv):
    """ Sales Team Budget Line """
    _name = 'sale.budget.line'
    
    def _get_bs_presupuesto(self, cr, uid, ids, name, arg, context):
        res = {}
        return res
        
    def _get_monto_inicial(self, cr, uid, ids, name, arg, context):
        res = {}
        return res
        
    def _get_bs_inicial(self, cr, uid, ids, name, arg, context):
        res = {}
        return res
        
    def _get_monto_ejecutado(self, cr, uid, ids, name, arg, context):
        res = {}
        return res
                
    def _get_bs_ejecutado(self, cr, uid, ids, name, arg, context):
        res = {}
        return res
    
    _columns = {
        'name': fields.char('Descripcion', help = 'Código de la alerta', invisible = True),
        'budget_id': fields.many2one('sale.budget',"Presupuesto", invisible = True),
        'category_id': fields.many2one('product.category',"Generico", required=True),
        'monto_presupuesto': fields.float('Presupuesto', help="Cantidades de unidades presupuestadas"),
        'bs_presupuesto': fields.function(_get_bs_presupuesto, type='float', string='Presupuesto (Bs.)', help="Cantidad en Bs. de las unidades presupuestadas", store = True, invisible = True),
        'monto_inicial': fields.function(_get_monto_inicial, type='float', string='Presupuesto inicial', help="Cantidades de unidades presupuestadas inicialmente", store = True, invisible = True),
        'bs_inicial': fields.function(_get_bs_inicial, type='float', string='Presupuesto (Bs.) inicial', help="Cantidades en Bs. de unidades presupuestadas inicialmente", store = True, invisible = True),
        'monto_ejecutado': fields.function(_get_monto_ejecutado, type='float', string='Ejecutado', help="Cantidades de unidades ejecutadas del presupuesto", store = True, invisible = True),
        'bs_ejecutado': fields.function(_get_bs_ejecutado, type='float', string='Ejecutado (Bs.)', help="Cantidades en Bs. de unidades ejecutadas del presupuesto", store = True, invisible = True),
    }

sale_budget_line()
