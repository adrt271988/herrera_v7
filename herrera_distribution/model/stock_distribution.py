# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp import netsvc
from datetime import datetime
import time
from openerp.tools import float_compare

class stock_distribution(osv.osv):
    _name = "stock.distribution"
    _order = "date desc"

    def print_sada(self, cr, uid, ids, context = None):
	context = context and context or {}
	distribution = self.browse(cr, uid, ids[0], context)
	return {
                    'type': 'ir.actions.report.xml',
                    'datas': {'ids': ids,
                                'form': ids,
                                'report_type': 'pdf',
                                'model': 'stock.distribution'},
                    'report_name': 'stock.distribution.sada.report',
                }

    def prepare_reception(self, cr, uid, ids, context=None):
	context = context and context or {}
	view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'herrera_distribution', 'pre_reception_wizard_form')
	return {
		    'view_mode': 'form',
		    'view_id': view_id[1],
		    'view_type': 'form',
		    'res_model': 'pre.reception.wizard',
		    'type': 'ir.actions.act_window',
		    'target': 'new',
		    'context': context,
		}
    
    def _get_chained_pickings(self, cr, uid, ids, context=None):
        distro_lines = self.browse(cr, uid, ids[0], context).line_ids
        picking_ids = []
        # Recorremos las lineas del despacho
        for line in distro_lines:
            move_lines = line.picking_id.move_lines
            picking_set = set(map(lambda x: x.move_dest_id.picking_id.id, move_lines))
            picking_ids.extend(list(picking_set))
        return picking_ids
        
    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        pick_obj = self.pool.get('stock.picking')
        pick_ids = self._get_chained_pickings(cr, uid, ids, context=context)
        shop_id = self.browse(cr, uid, ids[0], context).shop_id.id
        journal_id = self.pool.get('account.journal').search(cr, uid, 
                      [('type','=','sale'),('shop_id','=',shop_id)])
        journal_id = journal_id and journal_id[0] or False
        inv_type = 'out_invoice'
        invoices = []
        group = False
	##### Validando existencia de facturas asociadas al pedido, causado por Re-envio de mercancía
	for pick in pick_obj.browse(cr, uid, pick_ids, context):
	    sale_invoices = pick.sale_id.invoice_ids
	    if sale_invoices:
		inv_states = map(lambda x: x.state, sale_invoices)
		if 'open' in inv_states:
		    pick_ids.remove(pick.id)
	#############################################################################################
        res = pick_obj.action_invoice_create(cr, uid, pick_ids,
                      journal_id, group, inv_type, context=context)
        for pick_id in res.keys():
            if type(res[pick_id]) is list:
                invoices.extend(res[pick_id])
            else:
                invoices.append(res[pick_id])
        self.write(cr, uid, ids[0], {'state': 'done'}, context)
        return invoices
    
    def set_confirm(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        
        if context is None:
            context = {}
        
        result = {}
        ctx = dict(context, active_model=self._name, active_ids=ids, active_id=ids[0])
        distro_lines = self.browse(cr, uid, ids[0], context).line_ids
        ok_all = all(map(lambda x : x.ok, distro_lines))
        if not ok_all:
            raise osv.except_osv(_('Warning!'), _('Hay renglones de pedidos sin confirmar, por favor verifique...!!!') )
        
        # Recorremos las lineas del despacho
        for line in distro_lines:
            picking_id = line.picking_id and line.picking_id.id or False
            move_lines = line.picking_id.move_lines
            # Hacemos 'Done' a los move
            for move in move_lines:
                move_obj.action_done(cr, uid, [move.id], context)
            if picking_id :
                picking_obj.action_move(cr, uid, [picking_id], context=context)
                # Haciendo 'Done' los pickings se dispara el albaran
                # hacia la ubicacion encadenada
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)
        # Confirmamos el despacho
        self.write(cr, uid, ids[0], {'state': 'confirmed'}, context)
        return True

    def set_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids[0], {'state': 'cancel'}, context)
        return True

    def validate(self, cr, uid, ids, context=None):
	context = context and context or {}
	distribution = self.browse(cr, uid, ids[0], context)
	request_obj = self.pool.get('mail.authorization.request')
	request = {}
	if not distribution.vehicle_id:
	    raise osv.except_osv(_('Warning!'), _('Ingrese vehículo para validar el Pre-Despacho!!!') )
	if not distribution.driver_id:
	    raise osv.except_osv(_('Warning!'), _('Ingrese chofer para validar el Pre-Despacho!!!') )
	if not distribution.direct:
	    total_weight = sum(map(lambda x: x.weight ,distribution.line_ids))
	    ### Rechazamos si la capacidad en kilogramos excede el peso limite del camion
	    if total_weight > distribution.vehicle_id.capacity_kgs:
		raise osv.except_osv(_('Warning!'), _('Excede las capacidades de peso del camión... No es posible crear el despacho!') )
	    ### POR HACER: Copiar condicion anterior para validar carga volumetrica
	    if total_weight < distribution.vehicle_id.min_capacity_kgs:
		state = 'waiting_operative'
		warning = 'Requiere autorización de la Gerencia Operativa para confirmar este despacho debido a que no cumple con las capacidades de peso y volumétricas del camión'
		obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_distribution_minimum_load')])
		auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
		request = {
			'name': 'Solicitud de despacho por debajo de la carga mínima del camión',
			'authorization_id': auth_id,
			'user_id': uid,
			'ref': distribution.name,
			'model_id': self.pool.get('ir.model').search(cr, uid, [('name','=','stock.distribution')])[0],
			'request_date': datetime.today(),
			'state': 'wait',
			'res_id': ids[0],
			}
	    if request:
		request_obj.create(cr, uid, request)
		self.write(cr, uid, ids[0], {'state': state, 'warning': warning}, context)
	    else:
		self.write(cr, uid, ids[0], {'state': 'authorized'}, context)
	else:
	    self.write(cr, uid, ids[0], {'state': 'authorized'}, context)
        return True

    def force(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        request_obj = self.pool.get('mail.authorization.request')
        distro_name = self.browse(cr, uid, ids[0], context).name
        request_id = request_obj.search(cr, uid, [('ref','=',distro_name)])[0]
        if request_obj.browse(cr, uid, request_id, context).state == 'done':
            self.write(cr, uid, ids, {'state': 'authorized'})
        else:
            raise osv.except_osv(_('Warning!'), _('Aún el despacho no ha sido autorizado por el Responsable!!!') )
        return True

    def action_view_invoice_lot(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = {}
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        lot_obj = self.pool.get('account.invoice.lot')
        name = self.browse(cr, uid, ids[0], context=context).name
        data_id = mod_obj.get_object_reference(cr, uid, 'herrera_invoice', 'account_invoice_lot_act')
        data_id = data_id and data_id[1] or False
        view_id = mod_obj.get_object_reference(cr, uid, 'herrera_invoice', 'account_invoice_lot_form')
        lot_ids = lot_obj.search(cr, uid, [('origin','like',name)], context=context)
        if not lot_ids:
            raise osv.except_osv(_('Acción inválida!'), _('No se encontró ningún lote asociado a este despacho... Por favor contacte a su administrador'))
        result = act_obj.read(cr, uid, [data_id], context=context)[0]
        result['views'] = [(view_id and view_id[1] or False, 'form')]
        result['res_id'] = lot_ids and lot_ids[0] or False
        return result
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        invoice_ids = self.create_invoice(cr, uid, ids, context=context)
        if context is None:
            context = {}
        context.update({
            'active_model': 'account.invoice',
            'active_ids': invoice_ids,
            'active_id': len(invoice_ids) and invoice_ids[0] or False,
            'origin': self.browse(cr, uid, ids[0], context=context).name
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.control.number',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
        
    def _get_amount(self, cr, uid, ids, field_name, arg, context):
        res = dict.fromkeys(ids, 0)
        distro = self.browse(cr, uid, ids[0], context)
        for line in distro.line_ids:
            for detail in line.route_id.detail_ids:
                if distro.driver_id.driver_type == 'C':
                    if detail.type == 'CC':
                        res[ids[0]] += float(detail.weight * line.weight) + float(detail.volume * line.volume) + float(detail.boxes * line.payment_independent_units)
                else:
                    if detail.type == 'CF':
                        res[ids[0]] += float(detail.weight * line.weight) + float(detail.volume * line.volume) + float(detail.boxes * line.payment_independent_units)
        return res

    def _compute_total_weight(self, cr, uid, ids, name, args, context=None):
        res = {}
        for distribution in self.browse(cr, uid, ids, context=context):
	    res[distribution.id] = sum(map(lambda x: x.weight ,distribution.line_ids))
        return res
    
    _columns = {
        'name' : fields.char('Número de Despacho', size = 10, required = True),
        'warning' : fields.char('Mensaje', size = 200),
        'state':fields.selection([
	    ('draft', 'Pre-Despacho'),
            ('waiting_admin', 'Esperando Autorización por Administración'),
            ('waiting_operative', 'Esperando Autorización por Operaciones'),
            ('authorized', 'Autorizado'),
            ('confirmed', 'Confirmado'),
            ('done', 'Facturado'),
            ('pre-reception', 'Pre-Recepción'),
            ('closed', 'Recepcionado'),
            ('cancel', 'Cancelado'),
            ], 'Status', select=True),
        'vehicle_id' :fields.many2one('fleet.vehicle', 'Camión'),
        'driver_id' :fields.many2one('fleet.drivers', 'Chofer'),
        'shop_id' :fields.many2one('sale.shop', 'Sucursal', required=True),
        'date': fields.datetime('Fecha de Despacho', required=True),
        'line_ids': fields.one2many('stock.distribution.line', 'distro_id', 'Pedidos Asociados'),
        'amount': fields.function(_get_amount, type='float', string='Flete Estimado', help='Monto (Bs.) estimado del flete del despacho', store= True),
        'direct' :fields.boolean('Despacho directo'),
	'total_weight': fields.function(_compute_total_weight, type='float', string='Total Kgrs.', store=True),
        #~ 'moves_confirmed' : fields.function(_get_count, type='boolean', string='Movimientos confirmados a despachar', store=True),
    }

    _defaults = {
        'date': fields.date.context_today,
        'direct': False,
    }

stock_distribution()

class stock_distribution_line(osv.osv):
    _name = "stock.distribution.line"
    _order = "id asc"
    
    def _check_moves(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = this.picking_id.move_lines and \
                all([move.distribution_confirm for move in this.picking_id.move_lines]) 
        return res
        
    def _distribution_line_from_move(self, cr, uid, ids, context=None):
        move_brw = self.pool.get('stock.move').browse(cr, uid, ids, context=context)
        picking_ids = [move.picking_id.id for move in move_brw]
        return self.pool.get('stock.distribution.line').search(cr, uid, [('picking_id','in',picking_ids)], context=context)

    _columns = {
        'distro_id': fields.many2one('stock.distribution','Despacho'),
        'sale_id': fields.many2one('sale.order', 'Pedido', help = 'Pedido de Ventas Asociado'),
        'partner_id': fields.many2one('res.partner', 'Cliente', help = 'Cliente'),
        'state_id': fields.many2one('res.country.state', 'Estado', help = 'Estado'),
        'municipality_id': fields.many2one('res.municipality', 'Municipio', help = 'Municipio'),
        'sector_id': fields.many2one('res.sector', 'Sector', help = 'Sector'),
        'route_id': fields.many2one('freight.route', 'Ruta', help = 'Ruta del flete'),
        'product_qty' : fields.float("Cantidad UdV", help = 'Cantidad de Unidades de Venta'),
        'weight' : fields.float("Peso (Kgs)", help = 'Peso en Kilogramos'),
        'volume' : fields.float("Volumen", help = 'Volumen en m3'),
        'cost' : fields.float("Costo", help = 'Valoracion en bolivares, se usa el ultimo costo como base'),
        'payment_independent_units' : fields.float("Cantidad de Unidades de Pago Independiente", help = 'Cantidad de Unidades de Pago Independiente'),
        'date': fields.date('Fecha'),
        'picking_id': fields.many2one('stock.picking', 'Albarán Asociados'),
        'ok' : fields.function(_check_moves, type='boolean', string= "Confirmado", help = 'Todos los movimientos confirmados para despachar',
                    store={'stock.move': (_distribution_line_from_move, ['distribution_confirm'], 10)}),
    }

stock_distribution_line()
