# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp import netsvc
from datetime import datetime
import time
from openerp.tools import float_compare

class stock_reception(osv.osv):
    _name = "stock.reception"
    _order = "id desc"

    def _get_amount(self, cr, uid, ids, field_name, arg, context):
        res = dict.fromkeys(ids, 0)
        reception = self.browse(cr, uid, ids[0], context)
        for inv in reception.invoice_ids:
	    volume = weight = piu = 0.00
	    inv_volume = inv_weight = inv_piu = 0.00
	    rfd_volume = rfd_weight = rfd_piu = 0.00
	    if inv.reception_type in ('received','partial_refund'):
		### Calculamos kgrs, volumen y unidades independientes por facturas entregada
		for line in inv.invoice_line:
		    inv_weight += line.quantity*line.product_id.weight
		    inv_volume += line.quantity*line.product_id.volume
		    if line.product_id.ind_payment:
			inv_piu += line.quantity
		### Calculamos kgrs, volumen y unidades independientes por N/C
		if inv.child_ids:
		    for refund in inv.child_ids:
			for line in refund.invoice_line:
			    rfd_weight += line.quantity*line.product_id.weight
			    rfd_volume += line.quantity*line.product_id.volume
			    if line.product_id.ind_payment:
				rfd_piu += line.quantity
		### Obtenemos la diferencia de kgrs, volumen y piu entre Entregadas y N/C
		volume = inv_volume - rfd_volume
		weight = inv_weight - rfd_weight
		piu = inv_piu - rfd_piu
		if inv.partner_id.freight_route_id:
		    for detail in inv.partner_id.freight_route_id.detail_ids:
			if reception.distribution_id.driver_id.driver_type == 'C':
			    if detail.type == 'CC':
				res[ids[0]] += float(detail.weight * weight) + float(detail.volume * volume) + float(detail.boxes * piu)
			else:
			    if detail.type == 'CF':
				res[ids[0]] += float(detail.weight * weight) + float(detail.volume * volume) + float(detail.boxes * piu)
        return res
    
    def force(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for invoice in self.browse(cr, uid, ids[0], context).invoice_ids:
	    if invoice.reception_type == 'received':
		if invoice.reception_progress == 'waiting':
		    self.pool.get('account.invoice').write(cr, uid, [invoice.id], {'reception_progress': 'done'})
        return True

    def print_reception(self, cr, uid, ids, context = None):
	context = context and context or {}
	reception = self.browse(cr, uid, ids[0], context)
	return {
                    'type': 'ir.actions.report.xml',
                    'datas': {'ids': ids,
                                'form': ids,
                                'report_type': 'pdf',
                                'model': 'stock.reception'},
                    'report_name': 'stock.reception.report',
                }
    
    def force_reception(self, cr, uid, ids, context = None):
	context = context and context or {}
	reception = self.browse(cr, uid, ids[0], context)
	request_obj = self.pool.get('mail.authorization.request')
	request = {}
	obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_reception_invoice_adjust_amount')])
	auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
	request = {
		'name': 'Solicitud para recepción de facturas con diferencia por cobrar',
		'authorization_id': auth_id,
		'user_id': uid,
		'ref': reception.distribution_id.name,
		'model_id': self.pool.get('ir.model').search(cr, uid, [('name','=','stock.reception')])[0],
		'request_date': datetime.today(),
		'state': 'wait',
		'res_id': ids[0],
		}
	if request:
	    request_obj.create(cr, uid, request)
	return True
    
    def close_reception(self, cr, uid, ids, context = None):
	distribution_id = self.browse(cr, uid, ids[0], context).distribution_id.id
	self.pool.get('stock.distribution').write(cr, uid, [distribution_id], {'state':'closed'})
	view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'herrera_distribution', 'stock_distribution_form')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id[1],
            'res_model': 'stock.distribution',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'res_id': ids[0],
        }

    def _state(self, cr, uid, ids, name, args, context=None):
	res = {ids[0]: 'draft'}
	reception = self.browse(cr, uid, ids[0], context)
	obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','authorization_reception_invoice_adjust_amount')])
	auth_id = self.pool.get('ir.model.data').browse(cr,uid,obj_id[0]).res_id
	request_pool = self.pool.get('mail.authorization.request')
	request_id = request_pool.search(cr, uid, [('ref','=',reception.distribution_id.name),('authorization_id','=',auth_id)])
	distribution = self.pool.get('stock.distribution').browse(cr, uid, reception.distribution_id.id, context)
	rpt_progress = map(lambda x : x.reception_progress, reception.invoice_ids)
	inv_residuals = [x.residual for x in reception.invoice_ids if (x.reception_type in ['received'] and x.residual != 0.0)]
	if 'draft' not in rpt_progress:
	    if distribution.state not in ('closed'):
		if not request_id:
		    res = {ids[0]: inv_residuals and 'incomplete' or 'done'}
		else:
		    rq_state = request_pool.browse(cr, uid, request_id[0], context).state
		    res = {ids[0]: rq_state =="done" and 'done' or 'waiting'}
	    else:
		res = {ids[0]: 'closed'}
        return res
    
    _columns = {
        'name' : fields.char('Referencia', size = 10),
        'state': fields.function(_state, type='selection', selection=[('draft', 'Por Procesar'),
									('incomplete', 'Pago Incompleto'),
									('waiting', 'Esperando Autorización'),
									('done', 'Procesado'),
									('closed','Cerrada')], string='Status'),
        'shop_id' :fields.many2one('sale.shop', 'Sucursal'),
        'distribution_id' :fields.many2one('stock.distribution', 'Despacho'),
        'date': fields.datetime('Fecha de Recepción'),
        'invoice_ids': fields.one2many('account.invoice', 'reception_id', 'Líneas de Recepción'),
	'driver_amount': fields.function(_get_amount, type='float',string='Flete Chofer', help='Monto (Bs.) del flete del despacho',store=False),
    }

    _defaults = {
        'date': fields.date.context_today,
    }

stock_reception()
