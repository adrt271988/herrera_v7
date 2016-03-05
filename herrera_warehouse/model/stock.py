# -*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 OpenERP Venezuela (http://openerp.com.ve)
# All Rights Reserved.
# Programmed by: Israel Fermín Montilla  <israel@openerp.com.ve>
#
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
from openerp.osv import osv,fields
from openerp.tools.translate import _
from openerp import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class inherited_stock_move(osv.osv):
    """
    Herrera Customizations for stock.move model
    """
    _inherit = "stock.move"

    #funcion para inicializar el campo qty_available, este campo fue...
    #...creado solo para ser afectado por las funciones onchange
    def _get_qty_available(self,cr,uid,ids,field,arg,context=None):

        brw = self.browse(cr, uid, ids)
        res = {}
        for b in brw:
            res[b.id] = 0.0
        return res

    def action_scrap(self, cr, uid, ids, quantity, location_id, context=None):
        if context is None: context = {}
        res = []
        move_id = ids and ids[0] or False
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        move = self.browse(cr, uid, move_id, context=context)
        if move.picking_id and move.picking_id.type=='in':
            raise osv.except_osv(_('Advertencia!'),_('Disculpe, por los momentos no está permitido realizar desecho desde la recepcion, debe recibir el producto completamente y luego realizar una devolucion al proveedor por la cantidad dañada.'))
        else:
            c = (context or {}).copy()
            c['location'] = move.location_id.id
            qty_available = product_obj.browse(cr, uid, move.product_id.id, context=c).qty_available
            move_qty = move.product_qty
            new_move_qty = move_qty - quantity
            #se capturan los pickings encadenados a este
            move_ids = move_obj.search(cr, uid, [('id','!=',move.id),('origin','=',move.origin),('prodlot_id','=',move.prodlot_id.id),('state','not in',['done','cancel'])], context=context)
            if qty_available < quantity:
                raise osv.except_osv(_('Warning!'), _('La cantidad a desechar supera la existencia del producto'))
            if new_move_qty < 0 and context.get('deduce',False):
                raise osv.except_osv(_('Warning!'), _('La cantidad en el albaran no puede ser negativa'))
            res = super(inherited_stock_move,self).action_scrap(cr, uid, ids, quantity, location_id, context=context)
            if res and move_id and context.get('deduce',False) and new_move_qty >= 0:
                move_ids.append(move_id)
                if new_move_qty > 0:
                    self.write(cr, uid, move_ids, {'product_qty':new_move_qty}, context=context)
                else:
                    # ---modificar aqui--- No permite borrar elementos que no sean borrador 
                    self.action_cancel(cr, uid, move_ids, context=context)
        return res

    def action_transit(self, cr, uid, ids, context=None):
        """ Changes state to In Transit.
        """
        moves = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'transit'})
        return True
    
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move.
        @return: List of ids.
        """
        self.write(cr, uid, ids, {'state': 'confirmed'})
        # Desplazado al 'action_done' de stock.picking
        # moves = self.browse(cr, uid, ids, context=context)
        # self.create_chained_picking(cr, uid, moves, context)
        return []

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the moves and if all moves are cancelled it cancels the picking.
        @return: True
        """
        if not len(ids):
            return True
        if context is None:
            context = {}
        pickings = set()
        for move in self.browse(cr, uid, ids, context=context):
            if move.state in ('confirmed', 'waiting', 'assigned', 'draft'):
                if move.picking_id:
                    pickings.add(move.picking_id.id)
            if move.move_dest_id and move.move_dest_id.state == 'waiting':
                self.write(cr, uid, [move.move_dest_id.id], {'state': 'confirmed'}, context=context)
                if context.get('call_unlink',False) and move.move_dest_id.picking_id:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
        self.write(cr, uid, ids, {'state': 'cancel', 'move_dest_id': False}, context=context)
        if not context.get('call_unlink',False):
            for pick in self.pool.get('stock.picking').browse(cr, uid, list(pickings), context=context):
                if all(move.state == 'cancel' for move in pick.move_lines):
                    self.pool.get('stock.picking').write(cr, uid, [pick.id], {'state': 'cancel'}, context=context)

        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_trigger(uid, 'stock.move', id, cr)
        return True
    
    def _prepare_chained_picking(self, cr, uid, picking_name, picking, picking_type, moves_todo, context=None):
        values = super(inherited_stock_move, self)._prepare_chained_picking(cr, uid, picking_name, picking, picking_type, moves_todo, context=context)
        locations = map(lambda x: x.location_dest_id.id, picking.move_lines)
        location_set = set(locations)
        location_ids = list(location_set)
        if len(location_ids)==1:
            location_type = self.pool.get('stock.location').browse(cr, 
                uid, location_ids[0], context=context).internal_type
            values['location_id'] = location_ids[0]
            if location_type=='output' and picking_type == 'out':
                values['invoice_state'] = '2binvoiced'
        return values
        
    def _prepare_chained_move(self, cr, uid, delay, company_id, location_dest_id, picking_id, move, context=None):
        """Prepare the definition (values) to create a new chained move.

           :param str picking_name: desired new picking name
           :param browse_record picking: source picking (being chained to)
           :param str picking_type: desired new picking type
           :param list moves_todo: specification of the stock moves to be later included in this
            
        """
        res_company = self.pool.get('res.company')
        return {
                'location_id': move.location_dest_id.id,
                'location_dest_id': location_dest_id,
                'date': time.strftime('%Y-%m-%d'),
                'picking_id': picking_id,
                #~ 'state': 'waiting',
                'company_id': company_id or res_company._company_default_get(cr, uid, 'stock.company', context=context)  ,
                'move_history_ids': [],
                'date_expected': (datetime.strptime(move.date, '%Y-%m-%d %H:%M:%S') + relativedelta(days=delay or 0)).strftime('%Y-%m-%d'),
                'move_history_ids2': [],
                'sale_line_id': move.sale_line_id.id,
        }

    def create_chained_picking(self, cr, uid, moves, context=None):
        # Copiada del stock.py del modulo stock:
        # - se añadio la funcion _prepare_chained_move()
        # - el nuevo picking no es 'confirm' sino 'assigned'
        # - se eliminó la recursividad
        res_obj = self.pool.get('res.company')
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService("workflow")
        new_moves = []
        if context is None:
            context = {}
        seq_obj = self.pool.get('ir.sequence')
        for picking, chained_moves in self._chain_compute(cr, uid, moves, context=context).items():
            # We group the moves by automatic move type, so it creates different pickings for different types
            moves_by_type = {}
            for move in chained_moves:
                moves_by_type.setdefault(move[1][1], []).append(move)
            for todo in moves_by_type.values():
                ptype = todo[0][1][5] and todo[0][1][5] or location_obj.picking_type_get(cr, uid, todo[0][0].location_dest_id, todo[0][1][0])
                if picking:
                    # name of new picking according to its type
                    if ptype == 'internal':
                        new_pick_name = seq_obj.get(cr, uid,'stock.picking')
                    else :
                        new_pick_name = seq_obj.get(cr, uid, 'stock.picking.' + ptype)
                    pickid = self._create_chained_picking(cr, uid, new_pick_name, picking, ptype, todo, context=context)
                    # Need to check name of old picking because it always considers picking as "OUT" when created from Sales Order
                    old_ptype = location_obj.picking_type_get(cr, uid, picking.move_lines[0].location_id, picking.move_lines[0].location_dest_id)
                    if old_ptype != picking.type:
                        if old_ptype == 'internal':
                            old_pick_vals = {'name': seq_obj.get(cr, uid,'stock.picking'), 'type': 'internal', 'transfer_type': 'internal', 'invoice_state' : 'none' }
                        else :
                            old_pick_vals = {'name': seq_obj.get(cr, uid, 'stock.picking.' + old_ptype), 'type': old_ptype }
                        self.pool.get('stock.picking').write(cr, uid, [picking.id], old_pick_vals, context=context)
                else:
                    pickid = False
                for move, (loc, dummy, delay, dummy, company_id, ptype, invoice_state) in todo:
                    new_id = move_obj.copy(cr, uid, move.id, self._prepare_chained_move(cr, uid, delay, company_id, loc.id, pickid, move, context=context))
                    move_obj.write(cr, uid, [move.id], {
                        'move_dest_id': new_id,
                        'move_history_ids': [(4, new_id)]
                    })
                    new_moves.append(self.browse(cr, uid, [new_id])[0])
                if pickid:
                    #~ wf_service.trg_validate(uid, 'stock.picking', pickid, 'button_confirm', cr)
                    picking_obj.action_assign(cr, uid, [pickid])
        #~ if new_moves:
            #~ new_moves += self.create_chained_picking(cr, uid, new_moves, context)
        return new_moves
        

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(inherited_stock_move, self).default_get(cr, uid, fields, context=context)
        #~ res.update({'location_id': 11})
        return res
        
    def create(self, cr, uid, vals, context=None):
        if vals.get('type',False) == 'in' and \
            vals.get('measure',False) == False:
                vals.update({'measure': \
                self.pool.get('product.product').read(cr,uid, \
                vals['product_id'],['measure_po'])['measure_po'] })
        return super(inherited_stock_move, self).create(cr, uid, vals, context=context)

    _columns = {
        'qty_available': fields.function(_get_qty_available, type='float', string='Real Stock'),
        'code_search': fields.char('Código del Producto', select=True, help='Campo para Busqueda de productos por los codigos: EAN-13, EAN-14, COD-8 y Codigo de referencia'),
        #~ 'ref_sada': fields.related('picking_id', 'ref_sada', type='char', string='Guia SADA', readonly=True, store=True, help='Indica el numero de guia perteneciente a la mercancia recibida.'),
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Envío de Mercancía'), ('in', 'Recepción de Mercancía'),('internal', 'Interno/Transferencia')], string='Tipo de Envío'),
        'measure' : fields.selection([
            ('caja','CAJA'),
            ('fardo','FARDO'),
            ('2pack', 'DUOPACK'),
            ('3pack', 'TRIPACK'),
            ('4pack', 'TETRAPACK'),
            ('bulto','BULTO'),
            ('lata','LATA'),
            ('carton', 'CARTON'),
            ('unidad', 'UNIDAD'),
            ('docena', 'DOCENA'),
            ('estuche', 'ESTUCHE'),
            ('juego','JUEGO'),
            ('botella','BOTELLA'),
            ('galon', 'GALON'),
            ('kilos', 'KILOS'),
            ('tiras', 'TIRAS'),
            ('bolsa','BOLSA'),
            ('saco','SACO'),
            ('tobo', 'TOBO'),
            ('display', 'DISPLAY'),
            ('millar','MILLAR'),
            ('blister', 'BLISTER'),
            ('bandeja', 'BANDEJA'),
            ('exhibidor','EXHIBIDOR'),
            ('tarjeta','TARJETA'),
            ('gruesa', 'GRUESA'),
            ('tambor', 'TAMBOR'),
            ('paila', 'PAILA'),
            ], 'Unidad de medida'),
        'gline_id': fields.many2one('stock.global.line', 'Item de Global'),
        'state': fields.selection([('draft', 'New'),
                           ('cancel', 'Cancelled'),
                           ('waiting', 'Waiting Another Move'),
                           ('confirmed', 'Waiting Availability'),
                           ('assigned', 'Available'),
                           ('transit', 'In Transit'),
                           ('done', 'Done'),
                           ], 'Status', readonly=True, select=True,
         help= "* New: When the stock move is created and not yet confirmed.\n"\
               "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"\
               "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n"\
               "* Available: When products are reserved, it is set to \'Available\'.\n"\
               "* In Transit: When products are shipped, it is set to \'In Transit\'.\n"\
               "* Done: When the shipment is processed, the state is \'Done\'."),
        'to_refund':fields.boolean('Devolver', help= "Marcar para ser devuelta al proveedor"),
    }

    def onchange_search_product(self, cr, uid, ids, code_search):
        res = {}
        product_obj = self.pool.get('product.product')
        product_id = product_obj.search(cr, uid, ['|','|','|',('ean13','=',code_search),
                                                              ('ean14','=',code_search),
                                                              ('cod8','=',code_search),
                                                              ('default_code','=',code_search),])
        if product_id:
            value = {'product_id': product_id[0] }
            res.update({'value': value})

        else:
            warning = { 'title': _('Producto no Encontrado !'),
                        'message': _('El codigo %s no hace referencia a ningun producto existente. Por favor verifique que el codigo ingresado este correcto') % (code_search)
                       }
            res.update({'warning': warning})

        return res

    def onchange_location_id(self, cr, uid, ids, product_id, product_qty,
                          uom_id, loc_id=False, prodlot_id=False):
        """ On change of product quantity finds UoM and UoS quantities
        @param product_id: Product id
        @param product_qty: Changed Quantity of product
        @param product_uom: Unit of measure of product
        @param product_uos: Unit of sale of product
        @return: Dictionary of values
        """
        result = {}
        value = {'qty_available': 0.00 }
        result.update({'value': value})
        if not product_id or not loc_id:
            return result

        ctx = {}
        ctx['location'] = loc_id
        product_obj = self.pool.get('product.product')
        product_brw = product_obj.browse(cr, uid, product_id, context=ctx)
        value.update({'qty_available': product_brw.qty_available or 0.00 })
        result.update({'value': value})

        if prodlot_id and uom_id and product_qty:
            ctx['location_id'] = loc_id
            ctx.update({'raise-exception': True})
            uom_obj = self.pool.get('product.uom')
            product_obj = self.pool.get('product.product')
            product_uom = product_obj.browse(cr, uid, product_id, context=ctx).uom_id
            prodlot = self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id, context=ctx)
            location = self.pool.get('stock.location').browse(cr, uid, loc_id, context=ctx)
            uom = uom_obj.browse(cr, uid, uom_id, context=ctx)
            amount_actual = uom_obj._compute_qty_obj(cr, uid, product_uom, prodlot.stock_available, uom, context=ctx)
            qty_available = amount_actual and amount_actual * product_uom.factor or 0.00
            value = {}
            value.update({'qty_available': qty_available })
            warning = {}
            if (location.usage == 'internal') and (product_qty > (qty_available or 0.0)):
                warning = {
                    'title': _('Insufficient Stock for Serial Number !'),
                    'message': _('You are moving %.2f %s but only %.2f %s available for this serial number.') % (product_qty, uom.name, qty_available, uom.name)
                }
            if warning:
                result.update({'warning': warning})
            result.update({'value': value})

        return result

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        result = super(inherited_stock_move,self).onchange_product_id(cr, uid, ids, prod_id, loc_id, partner_id)
        #limpiamos el campo cada vez que se cambie de producto
        value = {'qty_available': 0.00 }
        if loc_id and prod_id:
            ctx = {}
            ctx['location'] = loc_id
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr, uid, prod_id, context=ctx)
            value.update({'qty_available': product_brw.qty_available or 0.00, 'measure': product_brw.measure_po or product_brw.measure})
            result['value'].update(value)
        return result

    def onchange_lot_id(self, cr, uid, ids, prodlot_id=False, product_qty=False,
                    loc_id=False, product_id=False, uom_id=False, context=None):

        result = super(inherited_stock_move,self).onchange_lot_id(cr, uid, ids, prodlot_id, product_qty, loc_id, product_id, uom_id, context=context)
        if not product_id or not prodlot_id or not loc_id:
            return result
        ctx = context and context.copy() or {}
        ctx['location_id'] = loc_id
        ctx.update({'raise-exception': True})
        uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        product_uom = product_obj.browse(cr, uid, product_id, context=ctx).uom_id
        prodlot = self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id, context=ctx)
        location = self.pool.get('stock.location').browse(cr, uid, loc_id, context=ctx)
        uom = uom_obj.browse(cr, uid, uom_id, context=ctx)
        amount_actual = uom_obj._compute_qty_obj(cr, uid, product_uom, prodlot.stock_available, uom, context=ctx)
        qty_available = amount_actual and amount_actual * product_uom.factor or 0.00
        value = {}
        value.update({'qty_available': qty_available })
        warning = {}
        if (location.usage == 'internal') and (product_qty > (qty_available or 0.0)):
            warning = {
                'title': _('Insufficient Stock for Serial Number !'),
                'message': _('You are moving %.2f %s but only %.2f %s available for this serial number.') % (product_qty, uom.name, qty_available, uom.name)
            }
        if warning:
            result.update({'warning': warning})
        result.update({'value': value})

        return result

    def onchange_quantity(self, cr, uid, ids, product_id, product_qty,
                          uom_id, product_uos, loc_id=False, prodlot_id=False):
        """ On change of product quantity finds UoM and UoS quantities
        @param product_id: Product id
        @param product_qty: Changed Quantity of product
        @param product_uom: Unit of measure of product
        @param product_uos: Unit of sale of product
        @return: Dictionary of values
        """

        result = super(inherited_stock_move,self).onchange_quantity(cr, uid, ids, product_id, product_qty, uom_id, product_uos)
        if not product_id or not prodlot_id or not loc_id:
            return result
        ctx = {}
        ctx['location_id'] = loc_id
        ctx.update({'raise-exception': True})
        uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        product_uom = product_obj.browse(cr, uid, product_id, context=ctx).uom_id
        prodlot = self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id, context=ctx)
        location = self.pool.get('stock.location').browse(cr, uid, loc_id, context=ctx)
        uom = uom_obj.browse(cr, uid, uom_id, context=ctx)
        amount_actual = uom_obj._compute_qty_obj(cr, uid, product_uom, prodlot.stock_available, uom, context=ctx)
        qty_available = amount_actual and amount_actual * product_uom.factor or 0.00
        value = {}
        value.update({'qty_available': qty_available })
        warning = {}
        if (location.usage == 'internal') and (product_qty > (qty_available or 0.0)):
            warning = {
                'title': _('Insufficient Stock for Serial Number !'),
                'message': _('You are moving %.2f %s but only %.2f %s available for this serial number.') % (product_qty, uom.name, qty_available, uom.name)
            }
        if warning:
            result.update({'warning': warning})
        result.update({'value': value})

        return result

    def onchange_move_type(self, cr, uid, ids, type, context=None):
        if context is None: context = {}
        result = super(inherited_stock_move,self).onchange_move_type(cr, uid, ids, type, context=context)
        if 'domain' not in result: result.update({'domain': {}})
        obj_warehouse = self.pool.get('stock.warehouse')
        obj_location = self.pool.get('stock.location')
        obj_picking = self.pool.get('stock.picking')
        source_location = False
        dest_location = False
        location_list = []
        if type == 'internal':
            #TODO: Filtrar las ubicaciones de acuerdo a el shop de el usuario
            wrh_ids = obj_warehouse.search(cr, uid, [], context=context)
            abt_ids = obj_location.search(cr, uid, [('name','=','ABASTECIMIENTO BARCELONA')], context=context)
            for wrh_id in wrh_ids:
                location_list.extend(obj_picking._get_stockable_location(cr,uid,wrh_id,context=context))
            if location_list:
                result['domain'].update({'location_id':[('id','in',location_list)]})
            if abt_ids:
                source_location = abt_ids[0]
            if context.get('warehouse_dest_id',False):
                wrh_brw = obj_warehouse.browse(cr, uid, context['warehouse_dest_id'], context=context)
                # buscamos en las ubicacion stock la que tenga encadenada 
                # que en la mayoria de los casos es - ENTRADA -
                if wrh_brw.lot_stock_id.chained_location_id and 'domain' in result:
                    dest_location = wrh_brw.lot_stock_id.chained_location_id.id
                    result['domain'].update({'location_dest_id':[('id','in',[dest_location])]})
            result.update({'value':{'location_id': source_location , 'location_dest_id': dest_location }})
        return result
    
    _defaults = {
        'to_refund': 0,
    }
inherited_stock_move()

class inherit_stock_location(osv.osv):
    _inherit = 'stock.location'

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for location in self.browse(cr, uid, ids, context=context):
            #we may not know the level of the parent at the time of computation, so we
            # can't simply do res[location.id] = location.location_id.level + 1
            level = 0
            parent = location.location_id
            while parent:
                level += 1
                parent = parent.location_id
            res[location.id] = level
        return res
    
    _columns = {
        'name': fields.char('Location Name', size=64, required=True, translate=False),
        'level': fields.function(_get_level, string='Level', type='integer', store=True),
        'internal_type': fields.selection([('view', 'Vista'), ('hall', 'Pasillo'), ('picking', 'Picking'), ('in', 'Entrada'), ('output', 'Salida'), ('procurement', 'Abastecimiento'), ('alternate', 'Alterno'), ('reinstatement', 'Reintegro'),('consu','Consumibles')], 'Location Use If Internal', select = True),
    }

inherit_stock_location()

class inherited_stock_picking(osv.osv):
    """
    Herrera Customizations for stock.picking model
    """
    _inherit = "stock.picking"

    def _get_price_unit_invoice(self, cursor, user, move_line, type):
        if move_line.purchase_line_id:
            return move_line.purchase_line_id.price_base
        elif move_line.sale_line_id:
            return move_line.sale_line_id.price_unit
        return super(inherited_stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)

    def _get_order_discount(self, cursor, user, picking, type):
        discount = 0.0
        purchase_brw = picking.purchase_id
        if purchase_brw and  hasattr(purchase_brw,'discount'):
            discount = purchase_brw.discount
        return discount
        
    def _get_shop_by_location(self, cr, uid, location_id, context = None):
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
        
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        invoice_vals = super(inherited_stock_picking, self)._prepare_invoice(cr, uid,
            picking, partner, inv_type, journal_id, context=context)
        
        #calculo de la fecha de vencimiento a partir de la fecha de recepcion
        date_ref = picking.reception_date and picking.reception_date or picking.date_done or picking.date ### Si no existe date_done tomamos la fecha de creacion
        date_recep = datetime.strptime(date_ref[0:19],"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        pterm_list = self.pool.get('account.payment.term').compute(cr, uid, invoice_vals['payment_term'], value=1, date_ref=date_recep)
        shop = False
        if picking.purchase_id:
            shop = self._get_shop_by_location(cr, uid, picking.purchase_id.location_id.id) or False

        if pterm_list:
            pterm_list = [line[0] for line in pterm_list]
            pterm_list.sort()
            date_due = pterm_list[-1]
            
        invoice_vals.update({
            'discount': self._get_order_discount(cr, uid, picking, inv_type),
            'reception_date': picking.reception_date,
            'date_due': date_due,
            'shop_id': shop and shop[0] or False,
            'date_document': picking.purchase_id.date_order
        })
        return invoice_vals

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        invoice_line_vals = super(inherited_stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, 
            move_line, invoice_id, invoice_vals, context=context)
        invoice_line_vals.update({
            'measure': move_line.measure,
            'price_unit': self._get_price_unit_invoice(cr, uid, move_line, invoice_vals['type']),
            #~ 'discount': self._get_discount_invoice(cr, uid, move_line),
            'to_refund': move_line.to_refund,            
        })
        
        return invoice_line_vals
    
    # action_invoice_create ha sido copiada original de addons para la  
    # correcta ejecucion de las herencias de: [_prepare.., get_price..,]
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
            if isinstance(partner, int):
                partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
            if not partner:
                raise osv.except_osv(_('Error, no partner!'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                if move_line.state == 'cancel':
                    continue
                if move_line.scrapped:
                    # do no invoice scrapped products
                    continue
                vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                invoice_id, invoice_vals, context=context)
                if vals:
                    invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                    self._invoice_line_hook(cr, uid, move_line, invoice_line_id)

            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)
        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced',
            }, context=context)
            
        # Chequeamos las lineas de factura por si es necesaria dividirla
        for pick in self.browse(cr, uid, res.keys(), context=context):
            inv = invoice_obj.browse(cr, uid, res[pick.id], context=context)
            if inv.type not in ["out_invoice","out_refund"]:
                continue
            inv_split = invoice_obj.split_invoice(cr, uid, [inv.id], context=context)
            if inv_split :
                res[pick.id] = inv_split[inv.id]
                res[pick.id].append(inv.id)
        return res

    def _get_warehouse_by_picking(self, cr, uid, picking_id, context=None):
        warehouse_id = False
        picking_brw = self.browse(cr, uid, picking_id, context = context)
        pick_type = context.get('default_type', False) or picking_brw.type
        if pick_type and pick_type == 'in':
            warehouse_id = picking_brw.purchase_id and picking_brw.purchase_id.warehouse_id.id
        elif pick_type and pick_type == 'internal':
            warehouse_id = picking_brw.warehouse_dest_id and picking_brw.warehouse_dest_id.id
        return warehouse_id
    
    def _get_childs_stockable(self, cr, uid, location_id, deep = 0, context=None):
        location_obj = self.pool.get('stock.location')
        level_ids = []
        location_brw = location_obj.browse(cr, uid, location_id)
        next_level_ids = location_obj.search(cr, uid, [('location_id','=',location_id)])
        #~ print '****** deep *******',deep
        if next_level_ids:
            for next_level_id in next_level_ids:
                level_ids.extend(list(set(self._get_childs_stockable(cr, uid, next_level_id,deep+1))))
                #~ print '********* level_ids ********',level_ids
        else:
            level_ids.append(location_id)
        
        return level_ids
    
    def _get_stockable_location(self, cr, uid, wrh_id = False, context=None):
        """ Return a list of stockable locations depending of warehouse
        """
        context = context or {}
        obj_location = self.pool.get('stock.location')
        obj_warehouse = self.pool.get('stock.warehouse')
        where = []
        location_ids = []
        # para un warehouse particular
        if wrh_id:
            wrh_brw = obj_warehouse.browse(cr, uid, wrh_id, context=context)
            where.append(('location_id','=',wrh_brw.lot_stock_id.id))
            # buscamos las ubicaciones internas del stock, obviando la que 
            # tenga encadenada que en la mayoria de los casos es - ENTRADA -
            if wrh_brw.lot_stock_id.chained_location_id:
                where.append(('id','!=',wrh_brw.lot_stock_id.chained_location_id.id))
            for loc in obj_location.search(cr, uid, where):
                location_ids.extend(self._get_childs_stockable(cr, uid, loc))
        # si no se preselecciono un warehouse, buscamos en todos
        else:
            for wrh_id in obj_warehouse.search(cr, uid, [], context=context):
                wrh_brw = obj_warehouse.browse(cr, uid, wrh_id, context=context)
                where.append(('location_id','=',wrh_brw.lot_stock_id.id))
                # buscamos las ubicaciones internas del stock, obviando la que 
                # tenga encadenada que en la mayoria de los casos es - ENTRADA -
                if wrh_brw.lot_stock_id.chained_location_id:
                    where.append(('id','!=',wrh_brw.lot_stock_id.chained_location_id.id))
                for loc in obj_location.search(cr, uid, where):
                    location_ids.extend(self._get_childs_stockable(cr, uid, loc))
        # mapemos las ubicaciones encontradas
        location_brw = obj_location.browse(cr, uid, location_ids, context=context)
        l = map(lambda x: x.id, location_brw)
        return l
    
    def _get_locations(self, cr, uid, ids, field_name, args, context=None):
        """ Create a dictionary with ids pickings and their browse item 
        """
        context = context or {}
        res = {}
        picking_id = context.get('active_ids', False)
        wrh_id = picking_id and self._get_warehouse_by_picking(cr, uid, picking_id[0], context=context)
        if wrh_id:
            res = {}.fromkeys(ids,self._get_stockable_location(cr,uid,wrh_id,context=context))
        return res
    
    def create(self, cr, uid, vals, context=None):
        # Validacion de los move_lines
        move_lines = []
        def has_line(product_id, prodlot_id, location_id, location_dest_id):
            exists = False
            for line in move_lines:
                if not exists:
                    exists = line['product_id'] == product_id \
                     and line['prodlot_id'] == prodlot_id \
                     and line['location_id'] == location_id \
                     and line['location_dest_id'] == location_dest_id
            return exists
        if vals.get('type') == 'internal':
            for line in vals.get('move_lines',{}):
                if line and 'product_id' in line and 'prodlot_id' in line and 'location_id' in line and 'location_dest_id' in line:
                    if has_line(line['product_id'], line['prodlot_id'], line['location_id'], line['location_dest_id']):
                        raise osv.except_osv(_('Error de dupliciadad!'),_('Posee al menos un producto con mas de una linea de igual N° de lote. Elimine una de las lineas y edite la linea restante si es necesario.'))
                    else:
                        move_lines.append(line)
        return  super(inherited_stock_picking, self).create(cr, uid, vals, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        # Copiado del modulo stock
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in pickings:
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, 
                context=context)
        return True
    
    def action_move(self, cr, uid, ids, context=None):
        # Copiado del modulo stock y solo se agrego state 'transit'
        for pick in self.browse(cr, uid, ids, context=context):
            todo = []
            for move in pick.move_lines:
                
                if move.state == 'draft':
                    self.pool.get('stock.move').action_confirm(cr, uid, 
                        [move.id], context=context)
                    todo.append(move.id)
                elif move.state in ('transit','assigned','confirmed'):
                    todo.append(move.id)
            if len(todo):
                self.pool.get('stock.move').action_done(cr, uid, todo,
                        context=context)
        return True
            
    def action_done(self, cr, uid, ids, context=None):
        res = super(inherited_stock_picking,self).action_done(cr, uid, 
            ids, context=context)
        # Personalizamos y retornamos funcion original de action_done
        for pick in self.browse(cr, uid, ids, context=context):
            todo = []
            for move in pick.move_lines:
                if move.state == 'done':
                    todo.append(move)
            if len(todo):
                self.pool.get('stock.move').create_chained_picking(cr, 
                        uid, todo, context=context)
            if pick.type == 'out':
                # Tomar en cuenta que cada venta genera 3 pickings OUT
                # 1. Pasillo a Picking
                # 2. Picking a Salida
                # 3. Salida a Cliente
                # PROPUESTA: convertir los dos primeros en INTERNAL
                print 'stock.picking,action_done:: Poner aqui asiento contable'
        return res
        
    def action_transit(self, cr, uid, ids, context=None):
        """ En transferencias externas se aplica el estado 'En transito' 
            para indicar que el albarán no esta fisicamente dentro de 
            la compañia.
        @return: True
        """
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'transit'})
        todo = []
        for picking in pickings:
            for r in picking.move_lines:
                if r.state == 'assigned':
                    todo.append(r.id)
        #~ todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            self.pool.get('stock.move').action_transit(cr, uid, todo, 
                context=context)
        return True
        
    def force_transit(self, cr, uid, ids, *args):
        """ Confirms picking directly from draft state.
        @return: True
        """
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids):
            if not pick.move_lines:
                raise osv.except_osv(_('Error!'),_('You cannot process picking without stock moves.'))
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_transit', cr)
        return True
    
    def onchange_validate_line(self, cr, uid, ids, code):
        res = {}
        ctx = {}
        move_lines = []

        def has_line(product_id, prodlot_id, location_id, location_dest_id):
            exists = False
            for line in move_lines:
                if not exists:
                    exists = line['product_id'] == product_id \
                     and line['prodlot_id'] == prodlot_id \
                     and line['location_id'] == location_id \
                     and line['location_dest_id'] == location_dest_id
            return exists
                
        for vals in code:
            if vals[2] and 'product_id' in vals[2] and 'prodlot_id' in vals[2]:
                name = vals[2]['name']
                product_id = vals[2]['product_id']
                prodlot_id = vals[2]['prodlot_id']
                location_id = vals[2]['location_id']
                location_dest_id = vals[2]['location_dest_id']
                if has_line(product_id, prodlot_id, location_id, location_dest_id):
                    prodlot_name = prodlot_id and self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id, ctx).name
                    prodlot_mssg = prodlot_name and u'el N° de lote %s'%(prodlot_name) or u'sin N° de lote definido'
                    warning = { 'title': _('Advertencia !'),
                                'message': _('Ya existe una linea con el producto %s, %s y con ubicaciones origen/destino similares, se recomienda eliminar la linea reciente y editar su similar.') % (name,prodlot_mssg)
                              }
                    res.update({'warning': warning})
                    break
                else:
                    move_lines.append(vals[2])
        return res
    
    def _all_same_dest(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method update the invoice lot state taking into account
        invoice the print state.
        """
        context = context or {}
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            res[pick.id] = {
                'location_type': False, 
                'location_dest_type': False, 
            }
            location_all = map(lambda x: x.location_id.id, pick.move_lines)
            location_dest_all = map(lambda x: x.location_dest_id.id, pick.move_lines)
            location_set = set(location_all)
            location_dest_set = set(location_dest_all)
            location_ids = list(location_set)
            location_dest_ids = list(location_dest_set)
            if len(location_ids)==1:
                location_brw = pick.move_lines[0].location_id
                res[pick.id]['location_type'] = \
                        location_brw.usage == 'internal' and \
                        location_brw.internal_type
            if len(location_dest_ids)==1:
                location_dest_brw = pick.move_lines[0].location_dest_id
                res[pick.id]['location_dest_type'] = \
                        location_dest_brw.usage == 'internal' and \
                        location_dest_brw.internal_type
        return res
    
    def _get_picking_to_update(self, cr, uid, ids, context=None):
        context = context or {}
        move_obj = self.pool.get('stock.move')
        res = [brw.picking_id.id
               for brw in move_obj.browse(cr, uid, ids, context=context)]
        res = list(set(res))
        return res
        
    _columns = {
        'state': fields.selection([
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('auto', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('assigned', 'Ready to Transfer'),
                ('transit', 'In Transit'),
                ('done', 'Transferred'),
                ], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
                * Draft: not confirmed yet and will not be scheduled until confirmed\n
                * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                * Waiting Availability: still waiting for the availability of products\n
                * Ready to Transfer: products reserved, simply waiting for confirmation.\n
                * In Transit: products shipped, simply waiting for reception confirmation \n
                * Transferred: has been processed, can't be modified or cancelled anymore\n
                * Cancelled: has been cancelled, can't be confirmed anymore"""
            ),
        'transfer_type': fields.selection([
                ('internal', 'Interno'),
                ('external', 'Externo'),
                ], 'Tipo de transferencia', help="""
                * Interno: movimientos de mercancia dentro de la misma sucursal\n
                * Externo: transferencias de mercancia entre sucursales distintas"""
            ),
        'location_type': fields.function(
            _all_same_dest,
            type='char',
            string='Uso de ubicación',
            required=True,
            multi='internal_type',
            store={
                'stock.move': (_get_picking_to_update, 
                    ['location_id','picking_id'], 10)
            },
            help='Indicate the internal type of the Source Location.'),
        'location_dest_type': fields.function(
            _all_same_dest,
            type='char',
            string='Uso de ubicación destino',
            required=True,
            multi='internal_type',
            store={
                'stock.move': (_get_picking_to_update, 
                    ['location_dest_id','picking_id'], 10)
            },
            help='Indicate the internal type of the Destiny Location.'),
        'warehouse_dest_id': fields.many2one('stock.warehouse', 'Almacén destino', help="Almacén a donde deseamos enviar la transferencia"),
        'global_id': fields.many2one('stock.global', 'Global', help='Número de la global de origen'),
        'ref_sada':fields.char('N° Guia SADA',help='Indica el numero de guia perteneciente a la mercancia recibida.'),
        'reception_date': fields.datetime('Fecha de Recepción', help = "Fecha de Recepción de la Mercancía"),
    }
    
    def test_done(self, cr, uid, ids, context=None):
        """ Test whether the move lines are canceled or not.
        @return: True or False
        """
        return super(inherited_stock_picking,self).test_done(cr, uid, ids, context)
    
    def test_cancel(self, cr, uid, ids, context=None):
        """ Test whether the move lines are canceled or not.
        @return: True or False
        """
        return super(inherited_stock_picking,self).test_cancel(cr, uid, ids, context)

inherited_stock_picking()

    
# Redefinition of the new field in order to update the model stock.picking.in in the orm
# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed
class inherited_stock_picking_in(osv.osv):
    """
    Herrera Customizations for stock.picking model
    """
    _inherit = "stock.picking.in"

    _columns = {
        'ref_sada':fields.char('N° Guia SADA',help='Indica el numero de guia perteneciente a la mercancia recibida.'),
        'reception_date': fields.datetime('Fecha de Recepción', help = "Fecha de Recepción de la Mercancía"),
    }

inherited_stock_picking_in()

# Redefinition of the new field in order to update the model stock.picking.in in the orm
# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed
class inherited_stock_picking_out(osv.osv):
    """
    Herrera Customizations for stock.picking.out model
    """
    _inherit = "stock.picking.out"

    _columns = {
        'global_id': fields.many2one('stock.global', 'Global', help='Número de la global de origen'),
    }
    
    def create(self, cr, uid, vals, context=None):
        lines = []
        for line in vals.get('move_lines'):
            lines.append(str(line[2].get('product_id'))+'-'+str(line[2].get('prodlot_id')))
        
        for i in lines:
            if lines.count(i) > 1:
                raise osv.except_osv(_('Error!'),_('Posee al menos un producto con mas de una linea de igual N° de lote. Elimine una de las lineas y edite la linea restante si es necesario.'))
        return  super(inherited_stock_picking_out, self).create(cr, uid, vals, context=context)

    def onchange_validate_line(self, cr, uid, ids, code):
        res = {}
        ctx = {}
        product_ids = []

        for vals in code:
            if vals[2]:
                product_ids.append(str(vals[2].get('product_id'))+'-'+str(vals[2].get('prodlot_id')))

        for i in product_ids:
            if product_ids.count(i) > 1:
                prodlot_id = i.split('-')
                prodlot = self.pool.get('stock.production.lot').browse(cr, uid, [int(prodlot_id[1])], context=ctx)
                warning = { 'title': _('Advertencia !'),
                            'message': _('Ya existe una linea con el producto %s y el N° de lote %s, se recomienda eliminar la linea reciente y editar la linea anteriormente creada para dicho producto.') % (vals[2].get('name', False),prodlot[0].name)
                          }
                res.update({'warning': warning})
                return res
        return True
    
    def _get_suppliercode(self, cr , uid, info, product_id, context = None):
        info_ids = info.search(cr, uid, [('product_id','=',product_id)])
        product_code = ''
        if info_ids:
            if info.browse(cr, uid, info_ids[0], context).product_code:
                product_code = info.browse(cr, uid, info_ids[0], context).product_code
        return product_code

    def _get_palette(self, cr, uid, product, product_id, product_qty, context = None):
        product_brw = product.browse(cr, uid, product_id, context)
        palette = product_brw.palette
        if palette:
            oper = float(product_qty/palette)
            palette_num = int(oper)
            decimal = abs(oper) - abs(int(oper))
            udv_qty = decimal * palette
            string = palette_num >= 1 and '%s paletas, con %s %s'%(palette_num, round(udv_qty), product_brw.measure) or ''
        return palette and string or ''
                
    def create_global(self, cr, uid, ids, context=None):
        if context is None:
                context = {}
        move_obj = self.pool.get('stock.move')
        supinfo_obj = self.pool.get('product.supplierinfo')
        product_obj = self.pool.get('product.product')
        products = []
        location_dest_id = 0
        global_id = False
        for picking_brw in self.browse(cr, uid, ids, context):
            if picking_brw.sale_id is not False and picking_brw.state == 'assigned' and picking_brw.invoice_state == '2binvoiced' and picking_brw.type == 'out':
                for move in picking_brw.move_lines:
                    if move.gline_id and move.gline_id.global_id.state in ('draft','confirmed'):
                        prod = move.name
                        sale = move.picking_id.sale_id.name
                        glbl = move.gline_id.global_id.name
                        raise osv.except_osv(_('No se pudo procesar la global'), _('El item %s del pedido %s ya fue asociado en la global %s'%(prod,sale,glbl)))
                    else:
                        location_dest_id = move.location_dest_id.id
                        if move.state == 'assigned' and self.pool.get('stock.warehouse').search(cr, uid, [('lot_output_id','=',location_dest_id)]):
                            product_id = move.product_id.id
                            if product_id not in products:
                                products.append(product_id)
        if products:
            global_lines = []
            num = 1
            for i in products:
                cr.execute("""SELECT product_uom, id, product_qty
                              FROM stock_move
                              WHERE location_dest_id=%s AND
                                            product_id=%s AND
                                            picking_id in %s AND
                                            state='assigned'
                              GROUP BY product_uom, id, picking_id
                           """,(location_dest_id, i, tuple(ids)))
                results = cr.dictfetchall()
                product_qty = 0
                moves_in_global = []
                for res in results:
                    product_qty += res.get('product_qty')
                    moves_in_global.append(res.get('id'))
                product_brw = self.pool.get('product.product').browse(cr, uid, i, context)
                move_name = move_obj.browse(cr, uid, moves_in_global[0], context).name
                gline = {
                    'name' : move_name,
                    'item' : str(num).zfill(3),
                    'product_id' : i,
                    'product_qty' : product_qty,
                    'real_qty': product_qty,
                    'uom_id' : product_brw.uom_id.id,
                    'weight' : float(product_qty*product_brw.weight),
                    'volume' : float((product_qty*product_brw.volume)/1000000),
                    'supplier_code' : self._get_suppliercode(cr, uid, supinfo_obj, i, context),
                    'palette': self._get_palette(cr, uid, product_obj, i, product_qty, context),
                    'move_ids' : [(6, 0, moves_in_global)],
                }
                num+=1
                global_lines.append((0,0,gline))
            global_vals = {
                'name' : self.pool.get('ir.sequence').get(cr, uid, 'stock.global'),
                'date' : datetime.now(),
                'state' : 'draft',
                'global_lines' : global_lines,
            }
            global_id = self.pool.get('stock.global').create(cr, uid, global_vals, context = context)
            self.create_hall_document(cr ,uid, global_id, context=context)
        else:
            raise osv.except_osv(_('No se pudo procesar la global'), _('No hay existencia en el sistema para los albaranes en el almacén!'))
        
        return global_id
    
    def create_hall_document(self, cr, uid, global_id, context = None):
        global_obj = self.pool.get('stock.global')
        warehouse_obj = self.pool.get('stock.warehouse')
        location_obj = self.pool.get('stock.location')
        supinfo_obj = self.pool.get('product.supplierinfo')
        product_obj = self.pool.get('product.product')
        locations = []
        halls = []
        names = []
        for gline in global_obj.browse(cr, uid, global_id, context).global_lines:
            for move in gline.move_ids:
                location_id = move.location_id.id
                if location_id not in locations:
                    locations.append(move.location_id.id)
                location_name = move.location_id.complete_name
                for split in location_name.split('/'):
                    if 'PASILLO' in split:
                        if split in location_name:
                            if split not in halls:
                                halls.append(split)
        for h in halls:
            num = 1
            hall_lines = []
            for lo in locations:
                if h in location_obj.browse(cr, uid, lo, context).complete_name:
                    cr.execute("""SELECT stock_move.product_id, stock_move.product_uom, stock_move.prodlot_id, sum(stock_move.product_qty) as product_qty
                                      FROM stock_move
                                      JOIN stock_global_line ON stock_global_line.id = stock_move.gline_id
                                      WHERE stock_move.location_id=%s
                                      AND stock_move.state='assigned'
                                      AND stock_global_line.global_id = %s
                                      GROUP BY stock_move.product_id, stock_move.product_uom, stock_move.prodlot_id
                               """,(lo, global_id))
                    results = cr.dictfetchall()
                    product_id = results[0].get('product_id')
                    product_brw = self.pool.get('product.product').browse(cr, uid, product_id, context)
                    product_qty = results[0].get('product_qty')
                    prodlot = results[0].get('prodlot_id')
                    lines = {
                            'name' : str(num).zfill(3),
                            'product_id' : product_id,
                            'product_qty' : product_qty,
                            'prodlot_id' : prodlot,
                            'uom_id' : product_brw.uom_id.id,
                            'supplier_code' : self._get_suppliercode(cr, uid, supinfo_obj, product_id, context),
                            'palette': self._get_palette(cr, uid, product_obj, product_id, product_qty, context),
                            'location_id': lo,
                            }
                    num+=1
                    hall_lines.append((0,0,lines))
            vals = {
                        'name' : self.pool.get('ir.sequence').get(cr, uid, 'stock.hall.document'),
                        'date' : datetime.now(),
                        'lines' : hall_lines,
                        'global_id' : global_id,
                        'hall' : h.strip(),
            }
            self.pool.get('stock.hall.document').create(cr, uid, vals, context = context)
        return True
    
    def action_view_global(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = {}
        global_ids = []
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        for picking_brw in self.browse(cr, uid, ids, context):
            if picking_brw.sale_id is not False and picking_brw.state == 'assigned' and picking_brw.invoice_state == '2binvoiced' and picking_brw.type == 'out':
                for move in picking_brw.move_lines:
                    if move.gline_id and move.gline_id.global_id.state in ('draft','confirmed'):
                        global_id = move.gline_id.global_id.id
                        if global_id not in global_ids:
                            global_ids.append(global_id)
        if not global_ids:
            global_ids = [self.create_global(cr, uid, ids, context=context)]
        result = mod_obj.get_object_reference(cr, uid, 'herrera_warehouse', 'stock_picking_global_act')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #choose the view_mode accordingly
        if len(global_ids) > 1:
            result['domain'] = "[('id','in',["+','.join(map(str, global_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'herrera_warehouse', 'stock_picking_global_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = global_ids and global_ids[0] or False
        return result
        
inherited_stock_picking_out()

class inherited_stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"
    
    
    def action_scrap(self, cr, uid, ids, quantity, location_id, context=None):
        """ Move the scrap/damaged product into scrap location
        @param cr: the database cursor
        @param uid: the user id
        @param ids: ids of stock move object to be scrapped
        @param quantity : specify scrap qty
        @param location_id : specify scrap location
        @param context: context arguments
        @return: Scraped lines
        """
        move_obj = self.pool.get('stock.move')
        #quantity should in MOVE UOM
        if quantity <= 0:
            raise osv.except_osv(_('Warning!'), _('Please provide a positive quantity to scrap.'))
        res = []
        for line in self.browse(cr, uid, ids, context=context):
            source_location = line.location_id
            if source_location.usage != 'internal':
                #restrict to scrap from a virtual location because it's meaningless and it may introduce errors in stock ('creating' new products from nowhere)
                raise osv.except_osv(_('Error!'), _('Forbidden operation: it is not allowed to scrap products from a virtual location.'))
            
            new_move = move_obj.create(cr,uid,{'name' : '[' + line.product_id.default_code + '] ' + line.product_id.name,
                                                        'product_id': line.product_id.id,
                                                        'product_qty': quantity,
                                                        'product_uos_qty': quantity,
                                                        'product_uom': line.product_uom.id,
                                                        'product_uos': line.product_uom.id,
                                                        'measure': line.product_uom.measure,
                                                        'prodlot_id': line.prod_lot_id.id,
                                                        'location_id': source_location.id,
                                                        'location_dest_id': location_id, #scrap location
                                                        },context=context)
            res += [new_move]
            move_obj.action_done(cr, uid, res, context=context)
        return res
        
inherited_stock_inventory_line()
