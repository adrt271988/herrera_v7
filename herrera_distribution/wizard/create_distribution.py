# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime

class create_distribution(osv.osv_memory):
    _name = "create.distribution"

    def _get_default_shop(self, cr, uid, context=None):
        shop_obj = self.pool.get('sale.shop')
        user_obj = self.pool.get('res.users')
        user_brw = user_obj.browse(cr, uid, uid, context=context)
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        shop_ids = shop_obj.search(cr, uid, [('company_id','=',company_id),('main','=',True)])
        return shop_ids[0]

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(create_distribution, self).default_get(cr, uid, fields_list, context)
        ids = context['active_ids']
        lines = []
        if ids:
            for pick_brw in self.pool.get('stock.picking').browse(cr, uid, ids, context):
                line = {
                    'sale_id' : pick_brw.sale_id and pick_brw.sale_id.id or '',
                    'partner_id': pick_brw.partner_id and pick_brw.partner_id.id or '',
                    'state_id': pick_brw.state_id and pick_brw.state_id.id or '',
                    'municipality_id': pick_brw.municipality_id and pick_brw.municipality_id.id or '',
                    'sector_id': pick_brw.sector_id and pick_brw.sector_id.id or '',
                    'route_id': pick_brw.partner_id.freight_route_id and pick_brw.partner_id.freight_route_id.id or '' ,
                    'product_qty' : pick_brw.product_qty,
                    'cost' : pick_brw.cost,
                    'weight' : pick_brw.weight,
                    'volume' : pick_brw.volume,
                    'date' : pick_brw.date,
                    'payment_independent_units': pick_brw.ind_payment_units,
                    'picking_id': pick_brw.id,
                    }
                lines.append((0,0,line))
            if lines:
                res.update({'line_ids': lines})
            if 'direct' in context:
                res.update({'direct': context['direct']})
        return res
    
    def create_distro(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        auth_obj = self.pool.get('mail.authorization')
        request_obj = self.pool.get('mail.authorization.request')
        distro_obj = self.pool.get('stock.distribution')
        lines = []
        total_weight = total_volume = total_cost = 0
        wzd_brw = self.browse(cr, uid, ids[0], context)
        for line in wzd_brw.line_ids:
            sale_id = line.sale_id.id
            total_weight += line.weight
            total_volume += line.volume
            lines.append((0,0, {
                'sale_id' : sale_id,
                'partner_id': line.partner_id.id,
                'state_id': line.state_id and line.state_id.id or '',
                'municipality_id': line.municipality_id and line.municipality_id.id or '',
                'sector_id': line.sector_id and line.sector_id.id or '',
                'route_id': line.route_id and line.route_id.id or '',
                'product_qty' : line.product_qty,
                'weight' : line.weight,
                'volume' : line.volume,
                'cost' : line.cost,
                'date' : line.date,
                'payment_independent_units': line.payment_independent_units,
                'picking_id': line.picking_id.id
                }))
            total_cost += line.cost
        
        ### Inicializamos las variables necesarias para guardar el despacho
        state = 'draft'
        warning = 'Sin incidencias!'
        vals = {}
        request = {}
        name = self.pool.get('ir.sequence').get(cr, uid, 'stock.distribution')
        ### Si no es despacho directo evaluamos si se generan autorizaciones
        if not wzd_brw.direct:
	    if wzd_brw.vehicle_id:
		### Rechazamos si la capacidad en kilogramos excede el peso limite del camion
		if total_weight > wzd_brw.vehicle_id.capacity_kgs:
		    raise osv.except_osv(_('Warning!'), _('Excede las capacidades de peso del camión... No es posible crear el despacho!') )
		
		### POR HACER: Copiar condicion anterior para validar carga volumetrica
		
		if total_weight < wzd_brw.vehicle_id.min_capacity_kgs:
		    state = 'waiting_operative'
		    warning = 'Requiere autorización de la Gerencia Operativa para confirmar este despacho debido a que no cumple con las capacidades de peso y volumétricas del camión'
		    obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_distribution_minimum_load')])
		    auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
		    request = {
			    'name': 'Solicitud de despacho por debajo de la carga mínima del camión',
			    'authorization_id': auth_id,
			    'user_id': uid,
			    'ref': name,
			    'model_id': self.pool.get('ir.model').search(cr, uid, [('name','=','stock.distribution')])[0],
			    'request_date': datetime.today(),
			    'state': 'wait',
			    }

            ### Evaluamos el costo total del despacho
            if total_cost > self.pool.get('res.company').browse(cr, uid, 1, context).merchandise_insured_amount:
                state = 'waiting_admin'
                warning = 'El costo total del despacho es Bs. %s...Requiere autorización de Administración para confirmar este despacho debido a que excede el monto que cubre la poliza de aseguramiento de mercancía'%total_cost
                obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_distribution_excess_insurance_policy')])
                auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
                request = {
                        'name': 'Solicitud de despacho con exceso de la poliza de aseguramiento de mercancía',
                        'authorization_id': auth_id,
                        'user_id': uid,
                        'ref': name,
                        'model_id': self.pool.get('ir.model').search(cr, uid, [('name','=','stock.distribution')])[0],
                        'request_date': datetime.today(),
                        'state': 'wait',
                        }
       
            vals.update({
                    'name' : name,
                    'date' : datetime.now(),
                    'state' : state,
                    'invoice_state': 'not_printed',
                    'warning' : warning,
                    'line_ids' : lines,
                    'shop_id' : wzd_brw.shop_id.id,
                    'driver_id' : wzd_brw.driver_id.id,
                    'vehicle_id' : wzd_brw.vehicle_id.id,
                    'direct' : False,
            })
        
        if not vals:
            vals.update({
                    'name' : self.pool.get('ir.sequence').get(cr, uid, 'stock.distribution'),
                    'date' : datetime.now(),
                    'state' : state,
                    'invoice_state': 'not_printed',
                    'warning' : warning,
                    'line_ids' : lines,
                    'shop_id' : wzd_brw.shop_id.id,
                    'direct' : True,
            })

        distro_id = distro_obj.create(cr, uid, vals, context=context)

        if request:
            request.update({'res_id': distro_id})
            request_obj.create(cr, uid, request)
        
        tree_obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','stock_distribution_tree')])
        tree_res_id = self.pool.get('ir.model.data').browse(cr,uid,tree_obj_id[0]).res_id
        return {
           'name': 'Despacho',
           'view_type': 'form',
           'view_mode': 'form,tree',
           'views': [(tree_res_id,'tree')],
           'res_model': 'stock.distribution',
           'type': 'ir.actions.act_window'
        }

    _columns = {
            'vehicle_id' :fields.many2one('fleet.vehicle', 'Camión'),
            'driver_id' :fields.many2one('fleet.drivers', 'Chofer'),
            'shop_id' :fields.many2one('sale.shop', 'Sucursal'),
            'date': fields.datetime('Fecha'),
            'line_ids' : fields.one2many('create.distribution.line', 'parent_id', 'Líneas de Wizard'),
            'direct' : fields.boolean('Despacho directo'),
    }

    _defaults = {
            'date': fields.date.context_today,
            'shop_id' : _get_default_shop,
            'direct' : False,
    }

create_distribution()

class create_distribution_line(osv.osv_memory):
    _name = "create.distribution.line"

    _columns = {
            'parent_id': fields.many2one('create.distribution','Wizard Padre'),
            'sale_id': fields.many2one('sale.order', 'Pedido', help = 'Pedido de Ventas Asociado'),
            'partner_id': fields.many2one('res.partner', 'Cliente', help = 'Cliente'),
            'state_id': fields.many2one('res.country.state', 'Estado', help = 'Estado'),
            'municipality_id': fields.many2one('res.municipality', 'Municipio', help = 'Municipio'),
            'route_id': fields.many2one('freight.route', 'Ruta', help = 'Ruta del flete'),
            'sector_id': fields.many2one('res.sector', 'Sector', help = 'Sector'),
            'cost' : fields.float("Costo", help = 'Valoracion en bolivares, se usa el ultimo costo como base'),
            'product_qty' : fields.float("Cantidad UdV", help = 'Cantidad de Unidades de Venta'),
            'weight' : fields.float("Peso (Kgs)", help = 'Peso en Kilogramos'),
            'volume' : fields.float("Volumen", help = 'Volumen en m3'),
            'payment_independent_units' : fields.float("Cantidad de Unidades de Pago Independiente", help = 'Cantidad de Unidades de Pago Independiente'),
            'picking_id': fields.many2one('stock.picking', 'Albarán Asociados', help = 'Picking'),
            'date': fields.date('Fecha'),
            }

create_distribution_line()
