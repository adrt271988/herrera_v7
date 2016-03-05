# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from datetime import datetime

class inherited_sale_order(osv.Model):
    _inherit = "sale.order"

    def eval_location(self, cr, uid, ids, context):
        if context is None:
            context = {}
        picking_obj = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        location_obj = self.pool.get('stock.location')
        qty_sales = {} #cantidades pedidas por producto
        pr_in_locations = {} #locaciones donde se encuentra cada producto
        ### Primero obtengo dos diccionarios: productos a analizar y productos en sus ubicaciones
        for sale_brw in self.browse(cr, uid, ids, context):
            for line in sale_brw.order_line:
                product_id = line.product_id.id
                if product_id not in qty_sales.keys():
                    qty_sales[product_id] = line.product_uom_qty
                else:
                    qty_sales[product_id] += line.product_uom_qty
                location_ids = picking_obj._get_stockable_location(cr, uid, sale_brw.shop_id.warehouse_id.id, context)
                locations = []
                for location_id in location_ids:
                    context['location'] = location_id
                    product_brw = product_obj.browse(cr, uid, product_id, context=context)
                    if product_brw.qty_available > 0.00:
                        locations.append(location_id)
                        pr_in_locations.update({product_id:locations})
        ### Luego recorremos los productos en analisis para obtener las cantidades en locaciones internas y en no internas 
        available = {} ## cantidades en locaciones internas por producto
        not_available = {} ## cantidades en locaciones no internas por producto
        for p in pr_in_locations.keys(): #Ahora recorremos los productos con existencia en almacen (internas o no internas)
            for location_id in pr_in_locations.get(p):
                context['location'] = location_id
                pr = product_obj.browse(cr, uid, p, context=context)
                qty_available = pr.qty_available
                internal_type = location_obj.browse(cr, uid, location_id, context).internal_type
                if internal_type == "hall":
                    if p not in available.keys():
                        available[p] = qty_available
                    else:
                        available[p] += qty_available
                if internal_type in ("procurement","reinstatement","alternate"):
                    if p not in not_available.keys():
                        not_available[p] = qty_available
                    else:
                        not_available[p] += qty_available
        res = {}
        ### Realizamos analisis de las variables para obtener los productos faltantes y cantidades minimas a reponer 
        for p in pr_in_locations.keys():
            if p not in available.keys():
                qty_to_move = qty_sales[p] > not_available[p] and not_available[p] or qty_sales[p]
                res.update({p: qty_to_move})
            else:
                if qty_sales[p] > available[p]:
                    res.update({p: qty_sales[p] - available[p]})
        return res
    
    def check_outside_stock(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        res = {}
        sale_id = ids[0]
        products = self.eval_location(cr, uid, ids, context=context)
        if products:
            res = {
                    'type': 'ir.actions.report.xml',
                    'datas': {  'ids': [sale_id],
                                'form': products,
                                'report_type': 'pdf',
                                'model': 'sale.order'},
                    'report_name': 'products.outside.stock',
            }
        return res
        
    def check_product_reserve(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        result = {}
        seq_obj = self.pool.get('ir.sequence')
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService('workflow')
        done = []
        back = []
        output = False
        sale_id = ids[0]
        # Confirmamos la orden para generar el picking
        wf_service.trg_validate(uid, 'sale.order', sale_id, 'order_confirm', cr)
        pick_ids = pick_obj.search(cr, uid, [('sale_id', '=', sale_id),('state','=','confirmed')])
        pick_brw = pick_obj.browse(cr, uid, min(pick_ids), context=context)
        move_ids = move_obj.search(cr, uid, [('picking_id','=', min(pick_ids))])
        for move in move_obj.browse(cr, uid, move_ids, context):
            if move.product_id.type == 'consu' or move.location_id.usage == 'supplier':
                if move.state in ('confirmed', 'waiting'):
                    done.append(move.id)
                continue
            if move.state in ('confirmed', 'waiting'):
                # Important: we must pass lock=True to _product_reserve() to avoid race conditions and double reservations
                res = self.pool.get('stock.location')._product_reserve(cr, uid, [move.location_id.id], move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                if res:
                    #_product_available_test depends on the next status for correct functioning
                    #the test does not work correctly if the same product occurs multiple times
                    #in the same order. This is e.g. the case when using the button 'split in two' of
                    #the stock outgoing form
                    done.append(move.id)
                    r = res.pop(0)
                    product_uos_qty = move_obj.onchange_quantity(cr, uid, ids, move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                    cr.execute('update stock_move set location_id=%s, product_qty=%s, product_uos_qty=%s, prodlot_id=%s, measure=%s where id=%s', (r[1], r[0],product_uos_qty,len(r)>2 and r[2], move.product_id.measure,move.id))
                    output = move.location_dest_id.id
                    while res:
                        r = res.pop(0)
                        product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, ids, move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                        move_id = move_obj.copy(cr, uid, move.id, {'product_uos_qty': product_uos_qty, 'product_qty': r[0], 'location_id': r[1], 'prodlot_id': len(r)>2 and r[2], 'measure': move.product_id.measure})
                        done.append(move_id)
                else:
                    back.append(move.id)
        # Si el pedido tiene reservados y backorders
        if done and back:
            # Capturamos el nombre del picking actual
            picking_name = seq_obj.get(cr, uid, 'stock.picking.%s'%(pick_brw.type))
            new_picking_name = pick_brw.name
            # Cambiamos el nombre del picking actual
            pick_obj.write(cr, uid, [pick_brw.id], 
                    {
                        'name': picking_name
                    })
            # Creamos un nuevo picking para los moves confirmados
            new_picking = pick_obj.copy(cr, uid, pick_brw.id,
                    {
                        'name': new_picking_name,
                        'move_lines' : [],
                        'state':'draft',
                        'location_dest_id': output,
                    })
            # En el picking actual almacenamos el backorder
            pick_obj.write(cr, uid, [pick_brw.id], 
                    {   
                        'backorder_id': new_picking
                    })
            # Asociamos los move confirmados al nuevo picking
            move_obj.write(cr, uid, done, 
                    {
                        'picking_id': new_picking,
                        'state': 'assigned',
                    })
            # Confirmamos el nuevo picking
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
            # Llamamos a escritura del workflow del picking nuevo
            wf_service.trg_write(uid, 'stock.picking', new_picking, cr)
        # Si el solo tiene reservados
        elif done:
            move_obj.write(cr, uid, done, {'state': 'assigned'})
            if output:
                pick_obj.write(cr, uid, [pick_brw.id], 
                        {
                            'location_dest_id': output,
                        })
            # Llamamos a escritura del workflow del picking actual
            wf_service.trg_write(uid, 'stock.picking', pick_brw.id, cr)
        return result
        
    def stock_analysis(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        res = self.check_outside_stock(cr, uid, ids, context=context)
        if not res:
            res = self.check_product_reserve(cr, uid, ids, context=context)
        return res
    
    def onchange_partner_id(self, cr, uid, ids, partner_id=False, context = False):
        result = super(inherited_sale_order,self).onchange_partner_id(cr, uid, ids, partner_id, context)
        if partner_id:
	    partner_brw = self.pool.get('res.partner').browse(cr, uid, partner_id, context)
            value = {'payment_condition': partner_brw.payment_condition.id }
            result['value'].update(value)
        return result
        
    def onchange_user_id(self, cr, uid, ids, user_id=False, partner_id=False, context = False):
        result = {}
        # Por hacer
        return result
        
    def _get_default_shop(self, cr, uid, context=None):
        shop_obj = self.pool.get('sale.shop')
        user_obj = self.pool.get('res.users')
        user_brw = user_obj.browse(cr, uid, uid, context=context)
        shop_id = hasattr(user_brw,'shop_id') and user_brw.shop_id.id
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        shop_ids = shop_obj.search(cr, uid, [('company_id','=',company_id),('main','=',True)], context=context)
        if not shop_ids:
            raise osv.except_osv(_('Error!'), _('There is no default shop for the current user\'s company!'))
        return shop_id or shop_ids[0]
    
    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(inherited_sale_order, self).default_get(cr, uid, fields_list, context)
        if 'shop_id' in res:
            res['shop_id'] = self._get_default_shop(cr, uid, context=context)
        return res

    def onchange_payment_condition(self, cr, uid, ids, payment_condition, context=None):
        if context is None: context = {}
        domain = {}
        if payment_condition:
            condition_brw = self.pool.get('account.payment.condition').browse(cr, uid, payment_condition)
            term_ids = map(lambda x : x.id, condition_brw.term_ids)
            domain = {'payment_term': [('id','in',term_ids)]}
        return {'domain': domain}
    
    def _check_credit_blocked(self, cr, uid, order):
        check = True
        data_obj = self.pool.get('ir.model.data')
        rqst_obj = self.pool.get('mail.authorization.request')
        data_id = data_obj.search(cr,uid,[('name','=','authorization_blocked_sale_order')])
        auth_id = data_obj.browse(cr,uid,data_id[0]).res_id
        rqst_id = rqst_obj.search(cr,uid,[('authorization_id','=',auth_id),('res_id','=',order.id)])
        if rqst_id:
            state = rqst_obj.browse(cr,uid,rqst_id[0]).state
            if state != 'done':
                check = False
        else:
            if self.pool.get('res.partner').browse(cr,uid,order.partner_id.id).credit_blocked:
                rqst_obj.create(cr, uid, {
                    'name': 'Solicitud para procesamiento de Pedido de Venta',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': order.name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': order.id,
                })
                check = False
        return check
    
    def _check_credit_limit(self, cr, uid, order):
        check = True
        data_obj = self.pool.get('ir.model.data')
        rqst_obj = self.pool.get('mail.authorization.request')
        data_id = data_obj.search(cr,uid,[('name','=','authorization_credit_limit_sale_order')])
        auth_id = data_obj.browse(cr,uid,data_id[0]).res_id
        rqst_id = rqst_obj.search(cr,uid,[('authorization_id','=',auth_id),('res_id','=',order.id)])
        if rqst_id:
            state = rqst_obj.browse(cr,uid,rqst_id[0]).state
            if state != 'done':
                check = False
        else:
            credit_limit = self.pool.get('res.partner').browse(cr,uid,order.partner_id.id).credit_limit
            # 40% (=1.4) de holgura sobre el credito normal del cliente
            real_credit_limit = credit_limit * 1.4
            if order.amount_total > real_credit_limit:
                rqst_obj.create(cr, uid, {
                    'name': 'Solicitud para procesamiento de Pedido de Venta',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': order.name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': order.id,
                })
                check = False
        return check
    
    def _check_global_limit(self, cr, uid, order):
        check = True
        data_obj = self.pool.get('ir.model.data')
        part_obj = self.pool.get('res.partner')
        rqst_obj = self.pool.get('mail.authorization.request')
        data_id = data_obj.search(cr,uid,[('name','=','authorization_global_limit_sale_order')])
        auth_id = data_obj.browse(cr,uid,data_id[0]).res_id
        rqst_id = rqst_obj.search(cr,uid,[('authorization_id','=',auth_id),('res_id','=',order.id)])
        if rqst_id:
            state = rqst_obj.browse(cr,uid,rqst_id[0]).state
            if state != 'done':
                check = False
        else:
            # Monto que adeuda el cliente sobre pedidos facturados
            amount = part_obj.browse(cr,uid,order.partner_id.id).credit
            # Pedidos pendientes por facturar
            partner_order_ids = self.search(cr,uid,[
                        ('partner_id','=',order.partner_id.id),
                        ('state','not in',['cancel',]),
                        ('invoice_exists','=',False)
            ])
            partner_orders = self.browse(cr,uid,partner_order_ids)
            for partner_order in partner_orders:
                # Sumamos tambien al monto los pedidos por facturar
                amount += partner_order.amount_total
            # Tomamos el valor de limite global del cliente
            global_limit = part_obj.browse(cr,uid,order.partner_id.id).global_limit
            # 30% (=1.3) de holgura sobre el credito global del cliente
            real_global_limit = global_limit * 1.3
            # Validamos el limite global
            if amount > real_global_limit:
                rqst_obj.create(cr, uid, {
                    'name': 'Solicitud para procesamiento de Pedido de Venta',
                    'authorization_id': auth_id,
                    'user_id': uid,
                    'ref': order.name,
                    'request_date': datetime.today(),
                    'state': 'wait',
                    'res_id': order.id,
                })
                check = False
        return check
    
    def test_credit(self, cr, uid, ids, context=None):
        context = context or {}
        data_obj = self.pool.get('ir.model.data')
        rqst_obj = self.pool.get('mail.authorization.request')
        check = True
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a sales order which has no line.'))
            check = all([self._check_credit_blocked(cr, uid, o),
                            self._check_credit_limit(cr, uid, o),
                            self._check_global_limit(cr, uid, o), ])
        return check
    
    def action_wait(self, cr, uid, ids, context=None):
        res = super(inherited_sale_order,self).action_wait(cr, uid, ids, context=context)
        #~ print 'wait %s'%res
        return res
        
    def action_button_approved(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_approved', cr)
        #~ print wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_approved', cr)
        return True
    
    def action_credit_except(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            #~ for line in this.order_line:
                #~ line.write({'state': 'exception'})
            #~ if this.state == 'invoice_except':
            this.write({'state': 'credit_except'})
        return True
        
    def set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            # Deleting the existing instance of workflow for SO
            wf_service.trg_delete(uid, 'sale.order', id, cr)
            wf_service.trg_create(uid, 'sale.order', id, cr)
        return True
    
    # Replace original function because with super don't work correctly
    def copy_quotation(self, cr, uid, ids, context=None):
        res = super(inherited_sale_order,self).copy_quotation(cr, uid, ids, context=context)
        # copy previous name at new sale order origin field
        prev_name = self.read(cr, uid, ids[0], ['name'])['name']
        if prev_name:
            self.write(cr, uid, res['res_id'], {'origin':prev_name})
        return res
        
    _columns = {
       'payment_condition': fields.many2one('account.payment.condition', 'Payment Condition'),
       'mode': fields.selection([
                ('manual', 'Manual'),
                ('auto', 'Automático'),
                ], 'Modo de emisión', help="""
                * Manual: Emitidos desde el formulario del sistema\n
                * Automático: Cargados desde interfaz externa"""
            ),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('approved', 'Quotation Approved'),
            ('credit_except', 'Credit Exception'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True,help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'credit_except': [('readonly', False)]}),
    }
    
    _defaults = {
        'mode': 'manual',
        'shop_id': _get_default_shop,
    }

class inherited_sale_order_line(osv.Model):
    _inherit = "sale.order.line"

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(inherited_sale_order_line,self).product_id_change(cr, uid,
                          ids, pricelist, product, qty, uom, qty_uos, uos, name,
                          partner_id, lang, update_tax, date_order, packaging, fiscal_position,
                          flag, context=context)
        if product:
            product_obj = self.pool.get('product.product')
            product = product_obj.browse(cr, uid, product, context)
            result = res['value']
            uom_id = product.uom_id.id or uom
            result['product_uom'] = uom_id
            result['measure'] = product.measure
            result['name'] = '[%s] %s %s' % (product.default_code,product.name,product.pack)
            if res.get('warning',False) and ( \
            res['warning']['message'].find('vende este producto') or \
            res['warning']['message'].find('sells this product') ):
                #elmininamos mensaje de warning innecesario
                res.pop('warning')
        return res

    _columns = {
            'measure' : fields.selection([
                    ('bandeja', 'BANDEJA'),
                    ('blister', 'BLISTER'),
                    ('bolsa','BOLSA'),
                    ('botella','BOTELLA'),
                    ('bulto','BULTO'),
                    ('caja','CAJA'),
                    ('carton', 'CARTON'),
                    ('display', 'DISPLAY'),
                    ('docena', 'DOCENA'),
                    ('2pack', 'DUOPACK'),
                    ('exhibidor','EXHIBIDOR'),
                    ('fardo','FARDO'),
                    ('galon', 'GALON'),
                    ('gramo', 'GRAMO'),
                    ('gruesa', 'GRUESA'),
                    ('juego','JUEGO'),
                    ('kilos', 'KILOS'),
                    ('millar','MILLAR'),
                    ('lata','LATA'),
                    ('paila', 'PAILA'),
                    ('saco','SACO'),
                    ('tambor', 'TAMBOR'),
                    ('tarjeta','TARJETA'),
                    ('4pack', 'TETRAPACK'),
                    ('tiras', 'TIRAS'),
                    ('tobo', 'TOBO'),
                    ('tonelada', 'TONELADA'),
                    ('3pack', 'TRIPACK'),
                    ('unidad', 'UNIDAD'),
                    ], 'Presentación', help="Especificación de la presentacion del producto"),    
    }
