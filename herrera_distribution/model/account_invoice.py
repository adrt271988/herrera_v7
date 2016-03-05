# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from openerp import netsvc
import re

class inherited_distribution_invoice(osv.osv):
    
    _inherit = 'account.invoice'
    _order = "nro_ctrl asc"

    def partial_compute_refund(self, cr, uid, ids, new_pick, context=None):
	##### ******** Funcion parecida a compute_refund, para realizar N/C parciales  *********
	##### ******** OpenERP solo crea N/C iguales a la Factura  *********
	context = context and context or {}
	### Obtenemos los productos del new_pick
	pick_pool = self.pool.get('stock.picking')
	products = []
	for move in pick_pool.browse(cr, uid, new_pick, context).move_lines:
	    products.append({move.product_id.id : move.product_qty})
	#~ product_ids = map(lambda x: x.product_id.id, move_lines)
	### Inicializando las variables
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
	refund_acc_id = self.pool.get('account.account').search(cr, uid, [('code','=','42001002')])
	invoice = self.browse(cr, uid, context.get('active_id'), context=context)
	mode = 'refund'
	period = invoice.period_id.id
	date = datetime.datetime.today()
	description = 'Devolución de producto por el cliente'
	company = res_users_obj.browse(cr, uid, uid, context=context).company_id
	journal_id = self.pool.get('account.journal').search(cr, uid, [('shop_id','=',invoice.reception_id.shop_id.id),('type','=','sale_refund')])[0]
	if invoice.state in ['draft', 'proforma2', 'cancel']:
	    raise osv.except_osv(_('Error!'), _('Cannot %s draft/proforma/cancel invoice.') % (mode))
	if invoice.reconciled:
	    raise osv.except_osv(_('Error!'), _('Cannot %s invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.') % (mode))
	### Utilizamos la funcion de OpenERP _prepare_refund para obtener el diccionario de valores de la N/C
	refund = self._prepare_refund(cr, uid, invoice, date, period, description, journal_id, context=context)
	### Creamos las lineas de la nota de credito, ya sea un renglon completo o una porcion del renglon
	refund_line = []
	for i in refund['invoice_line']:
	    invoice_line = i[2]
	    for product in products:
		product_id = invoice_line['product_id']
		if product.has_key(product_id):
		    refund_qty = product[product_id]
		    if invoice_line['quantity'] > refund_qty:
			invoice_line['quantity'] = refund_qty
			invoice_line['price_subtotal'] = float(refund_qty*invoice_line['price_unit'])
		    refund_line.append((0,0,invoice_line))
	### Actualizamos el diccionario de valores de la N/C con los nuevos valores
	refund.update({'parent_id': invoice.id, 'invoice_line': refund_line, 'account_id': refund_acc_id[0]})
	### Finalizamos con la creacion de la N/C
	refund_id = self.create(cr, uid, refund, context=context)
	refund_brw = self.browse(cr, uid, refund_id, context=context)
	self.write(cr, uid, [refund_brw.id], {'date_due': date, 'check_total': invoice.check_total})
	self.button_compute(cr, uid, [refund_id])
	return True
    
    def get_return_location_dest(self, cr, uid, shop, internal_type, context=None):
	##### ******** Funcion para obtener la ubicación destino de un stock.move segun su sucursal *********
	location_dest = False
	location_ids = self.pool.get('stock.location').search(cr, uid, [('internal_type','=',internal_type)])
	for l in location_ids:
	    shop_id = self._get_shop_by_location(cr, uid, l, context)
	    if shop == shop_id[0]:
		location_dest = l
	return location_dest
    
    def get_picking_by_moves(self, cr, uid, moves, context = None):
	##### ******** Funcion para la obtención del Picking relacionado a la factura *********
	##### ******** Retorna una lista con un Picking
	context = context and context or {}
	picks = []
	### Evaluamos los moves para obtener los pickings asociados
	for move in self.pool.get('stock.move').browse(cr, uid, moves, context):
	    pick_id = move.picking_id.id
	    if pick_id not in picks:
		picks.append(pick_id)
	return picks
    
    def _get_shop_by_location(self, cr, uid, location_id, context = None):
	##### ******** Funcion para la obtención del shop_id dada una ubicacion *********
        shp_id = False
        wrh_id = location_id and self.pool.get('stock.warehouse').search(cr, uid, ['|','|',('lot_input_id','=',location_id),('lot_stock_id','=',location_id),('lot_output_id','=',location_id)]) or False
        if not wrh_id:
            # si esta locacion pertenece a un encadenamiento tomamos como padre a su encadenado superior
            parent = self.pool.get('stock.location').search(cr, uid, [('chained_location_id','=',location_id)])
            parent = parent and parent[0] or False
            # si no tiene encadenamiento tomamos como parent a su padre
            parent = parent or self.pool.get('stock.location').browse(cr, uid, location_id).location_id.id 
            shp_id = parent and self._get_shop_by_location(cr, uid, parent) or shp_id
        return shp_id or wrh_id and self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',wrh_id[0])])

    def return_picking(self, cr, uid, invoice_id, moves, internal_type, context = None):
	##### ******** Funcion para Devolucion de Movimientos y Albaranes de una Factura Completa  *********
	##### ******** Retorna una lista de movimientos nuevos
	context = context and context or {}
	move_obj = self.pool.get('stock.move')
	pick_obj = self.pool.get('stock.picking')
	uom_obj = self.pool.get('product.uom')
	data_obj = self.pool.get('stock.return.picking.memory')
	act_obj = self.pool.get('ir.actions.act_window')
	model_obj = self.pool.get('ir.model.data')
	wf_service = netsvc.LocalService("workflow")
	inv_pool = self.pool.get('account.invoice')
	date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
	invoice_brw = inv_pool.browse(cr, uid, invoice_id, context)
	picks = self.get_picking_by_moves(cr, uid, moves, context)
	new_location = self.get_return_location_dest(cr, uid, invoice_brw.reception_id.shop_id.id, internal_type, context = context)
	### Se crea una copia del picking, new_pick
	new_moves = []
	for pick in pick_obj.browse(cr, uid, picks, context):
	    new_pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
	    new_pick = pick_obj.copy(cr, uid, pick.id, {
					    'name': _('%s-%s-return') % (new_pick_name, pick.name),
					    'move_lines': [],
					    'state':'draft', 
					    'type': 'in',
					    'date': date_cur, 
					    'invoice_state': 'none',
					    })
	    ### Se crea una copia de los moves y se asocia a new_pick
	    for m in pick.move_lines:
		returned_qty = m.product_qty
		new_move = move_obj.copy(cr, uid, m.id, {
					    'product_qty': returned_qty,
					    'product_uos_qty': uom_obj._compute_qty(cr, uid, m.product_uom.id, returned_qty, m.product_uos.id),
					    'picking_id': new_pick, 
					    'state': 'draft',
					    'location_id': m.location_dest_id.id, 
					    'location_dest_id': new_location,
					    'date': date_cur,
					})
		move_obj.write(cr, uid, [m.id], {'move_history_ids2':[(4,new_move)]}, context=context)
		new_moves.append(new_move)
	### Hacemos Done el new_pick y sus moves
	wf_service.trg_validate(uid, 'stock.picking', new_pick, 'button_confirm', cr) #confirm
        pick_obj.force_assign(cr, uid, [new_pick], context) #assign
	move_obj.action_done(cr, uid, new_moves, context) #done
	return True
    
    def get_moves_by_invoice(self, cr, uid, invoice_id, context=None):
	##### ******** Funcion que retorna una lista de moves, asociados a la factura generada por un despacho  *********
	context = context and context or None
	moves = []
	move_obj = self.pool.get('stock.move')
	order_id = False
	sale_line_ids = []
	### Consultamos los pedidos asociados a una factura
	cr.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel ' \
                'WHERE rel.invoice_id = %s limit 1' % invoice_id)
	result = cr.fetchone()
	if result:
	    order_id = result[0]
	if order_id:
	    sale_line_brw = self.pool.get('sale.order').browse(cr, uid, order_id, context).order_line
	    sale_line_ids = map(lambda x: x.id, sale_line_brw)
	if sale_line_ids:
	    for move_id in move_obj.search(cr, uid, [('sale_line_id','in', sale_line_ids)]):
		move_brw = move_obj.browse(cr, uid, move_id, context)
		if move_brw.location_dest_id.usage == 'customer': ### Verificamos que los move sean del tercer picking (destino: Clientes)
		    moves.append(move_id)
	return moves

    def cr_voucher(self, cr, uid, ids, context = None):
	context = context and context or None
	invoice_id = ids[0]
	invoice = self.browse(cr, uid, invoice_id, context)
	reception_type = invoice.reception_type
	move_obj = self.pool.get('stock.move')
	moves = self.get_moves_by_invoice(cr, uid, ids[0], context)
	### Invocamos al wizard de pago si el termino de pago de la factura es Inmediato
	if invoice.payment_term.id == 1: ## valor cableado
	    view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'herrera_distribution', 'account_payment_wizard_form')
	    context.update({'type':invoice.type,
			    'partner_id': invoice.partner_id.id,
			    'journal_id': invoice.journal_id.id,
			    'moves': moves,
			    'default_amount': invoice.amount_total})
	    return {
		    'view_mode': 'form',
		    'view_id': view_id[1],
		    'view_type': 'form',
		    'res_model': 'account.payment.wizard',
		    'type': 'ir.actions.act_window',
		    'target': 'new',
		    'context': context,
		}
	else:
	    if reception_type == 'received':
		move_obj.action_done(cr, uid, moves, context)
	    self.write(cr, uid, [invoice_id], {'reception_progress':'done'})
	    return True
	
    def process_line(self, cr, uid, ids, context = None):
	context = context and context or None
	invoice_id = ids[0]
	invoice = self.browse(cr, uid, invoice_id, context)
	move_obj = self.pool.get('stock.move')
	reception_type = invoice.reception_type
	moves = self.get_moves_by_invoice(cr, uid, ids[0], context)
	if reception_type == 'received':
	    self.write(cr, uid, [invoice_id], {'reception_progress':'waiting'})
	    return True
	if reception_type == 'rejected':
	    journal_id = self.pool.get('account.journal').search(cr, uid, [('shop_id','=',invoice.reception_id.shop_id.id),('type','=','sale_refund')])
	    context.update({'journal_id': journal_id and journal_id[0] or '', 'moves': moves})
	    view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_account_invoice_refund')
	    return {
			'view_mode': 'form',
			'view_id': view_id[1],
			'view_type': 'form',
			'res_model': 'account.invoice.refund',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': context,
		    }
	if reception_type == 'resent':
	    self.return_picking(cr, uid, invoice_id, moves, 'picking', context = context)
	    self.write(cr, uid, [invoice_id], {'reception_progress':'done'})
	    return {'type': 'ir.actions.act_window_close'}
	if reception_type == 'partial_refund':
	    picks = self.get_picking_by_moves(cr, uid, moves, context)
	    move_obj.action_done(cr, uid, moves, context)
	    view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_stock_return_picking_form')
	    context.update({'picking': picks and picks[0] or '', 'reception_type': reception_type})
	    return {
			'view_mode': 'form',
			'view_id': view_id[1],
			'view_type': 'form',
			'res_model': 'stock.return.picking',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': context,
		    }

    def _get_payment_condition(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
	    cr.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel ' \
                'WHERE rel.invoice_id = %s limit 1' % invoice.id)
	    result = cr.fetchone()
	    if result:
		order_id = result[0]
		sale = self.pool.get("sale.order").browse(cr, uid, order_id, context)
		res[invoice.id] = sale.payment_condition and sale.payment_condition.id or False
        return res

    _columns = {
                'reception_id': fields.many2one('stock.reception', "Recepción"),
		'reception_type' : fields.selection([
				    ('received', 'Entregada'),
				    ('rejected', 'Rechazada'),
				    ('resent', 'Reenvio'),
				    ('partial_refund', 'N.C. Parcial'),
				    ], 'Tipo de Recepción'),
		'reception_progress' : fields.selection([
				    ('draft', 'Por Procesar'),
				    ('waiting', 'Esperando Pago'),
				    ('done', 'Procesado'),
				    ], 'Status'),
		'payment_condition': fields.function(_get_payment_condition, type='many2one', relation='account.payment.condition', string='Condición de Pago', store=True),
                }
    
inherited_distribution_invoice()

class inherit_distribution_account_invoice_refund(osv.osv_memory):

    _inherit = 'account.invoice.refund'

    def default_get(self, cr, uid, fields_list, context=None):
	context = context and context or {}
	res = super(inherit_distribution_account_invoice_refund, self).default_get(cr, uid, fields_list, context)
	journal_id = context.get('journal_id')
	if journal_id:
	    res.update({'journal_id':journal_id})
        return res
    
    def invoice_refund(self, cr, uid, ids, context=None):
	moves = context.get('moves')
	invoice_id = context['active_id']
	if moves:
	    inv_pool = self.pool.get('account.invoice')
	    acc_id = self.pool.get('account.account').search(cr, uid, [('code','=','42001002')])
	    inv_pool.return_picking(cr, uid, invoice_id, moves, 'reinstatement', context = context)
	    res = super(inherit_distribution_account_invoice_refund,self).invoice_refund(cr, uid, ids, context=context)
	    if acc_id:
		refund_inv_id = int(res['domain'][1][2][0])
		inv_pool.write(cr, uid, [refund_inv_id], {'account_id': acc_id[0]})
	    inv_pool.write(cr, uid, [invoice_id], {'reception_progress':'done'})
	    return {'type': 'ir.actions.act_window_close'}
	else:
	    return super(inherit_distribution_account_invoice_refund,self).invoice_refund(cr, uid, ids, context=context)

inherit_distribution_account_invoice_refund()

class inherit_distribution_stock_return_picking(osv.osv_memory):

    _inherit = 'stock.return.picking'

    def default_get(self, cr, uid, fields, context=None):
	context = context and context or {}
	if context.get('picking'):
	    context['active_id'] = context['picking']
	return super(inherit_distribution_stock_return_picking,self).default_get(cr, uid, fields, context=context)
    
    def create_returns(self, cr, uid, ids, context=None):
	context = context and context or {}
	inv_pool = self.pool.get('account.invoice')
	if context.get('picking'):
	    context['active_id'] = context['picking']
	    res = super(inherit_distribution_stock_return_picking,self).create_returns(cr, uid, ids, context=context)
	    new_pick = max(int(c) for c in re.findall("\d+",res['domain']))
	    pick_pool = self.pool.get('stock.picking')
	    move_pool = self.pool.get('stock.move')
	    picking = pick_pool.browse(cr, uid, new_pick)
	    shop_id = picking.sale_id.shop_id.id
	    location_dest = inv_pool.get_return_location_dest(cr, uid, shop_id, 'reinstatement', context = context)
	    for new_move in picking.move_lines:
		move_pool.write(cr, uid, [new_move.id], {'location_dest_id': location_dest})
		move_pool.action_done(cr, uid, [new_move.id], context)
	    invoice_id = context['active_ids'][0]
	    context.update({'active_id':invoice_id})
	    inv_pool.partial_compute_refund(cr, uid, ids, new_pick, context=context)
	    inv_pool.write(cr, uid, [invoice_id], {'reception_progress':'waiting'})
	    return {'type': 'ir.actions.act_window_close'}
	else:
	    return super(inherit_distribution_stock_return_picking,self).create_returns(cr, uid, ids, context=context)

inherit_distribution_stock_return_picking()
