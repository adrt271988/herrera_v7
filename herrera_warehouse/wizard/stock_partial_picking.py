# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
import datetime, time
from openerp.osv import fields, osv
from tools.translate import _
from openerp import netsvc

class inherit_stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'

    def _check_date(self,cr,uid,ids,context=None):
        fmt = '%Y-%m-%d %H:%M:%S'
        wizard_brw = self.browse(cr,uid,ids[0],context=context)
        reception_string = wizard_brw.reception_date.split(" ")
        reception_substr = reception_string[-1].split(".")
        reception_string[-1] = reception_substr[0]
        reception_string = " ".join(reception_string)
        today = datetime.datetime.now()
        today_string = today.strftime(fmt)
        if datetime.datetime.strptime(reception_string,fmt) > datetime.datetime.strptime(today_string, fmt):
            raise osv.except_osv(_('Warning!'), _('La fecha ingresada debe ser menor a la fecha actual!!'))
        return True
    
    def _get_warehouse_by_picking(self, cr, uid, picking_id, context=None):
        picking_obj = self.pool.get('stock.picking')
        warehouse_id = False
        picking_brw = picking_obj.browse(cr, uid, picking_id, context = context)
        pick_type = context.get('default_type', False) or picking_brw.type
        if pick_type and pick_type == 'in':
            warehouse_id = picking_brw.purchase_id and picking_brw.purchase_id.warehouse_id.id
        elif pick_type and pick_type == 'internal':
            warehouse_id = picking_brw.warehouse_dest_id and picking_brw.warehouse_dest_id.id
        return warehouse_id
    
    def _get_last_level(self, cr, uid, location_id, context=None):
        location_obj = self.pool.get('stock.location')
        last_level = location_obj.browse(cr, uid, location_id).level
        next_level_id = location_obj.search(cr, uid, [('location_id','=',location_id)])
        if next_level_id:
            last_level = self._get_last_level(cr, uid, next_level_id[0])
        return last_level
    
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
    
    def _partial_move_for(self, cr, uid, move):
        partial_move = super(inherit_stock_partial_picking, self)._partial_move_for(cr, uid, move)
        qty = move.product_qty if move.state in ['assigned','transit'] or move.picking_id.type == 'in' else 0
        msr = move.measure
        rfd = move.to_refund
        partial_move.update(quantity=qty)
        partial_move.update(measure=msr)
        partial_move.update(to_refund=rfd)
        return partial_move
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(inherit_stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        loc_obj = self.pool.get('stock.location')
        config_obj = self.pool.get('stock.config.settings')
        config_ids = config_obj.search(cr, uid, [])
        config_id = config_ids and max(config_ids) or False
        config = config_id and config_obj.browse(cr, uid, config_id, context)
        picking_ids = context.get('active_ids', [])
        wrh_id = picking_ids and self._get_warehouse_by_picking(cr, uid, picking_ids[0], context=context)
        if wrh_id:
            res.update({'location_list': self._get_stockable_location(cr,uid,wrh_id,context=context) })
        if 'move_ids' in fields and picking_ids:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_ids[0], context=context)
            res.update({'transfer_type': picking.transfer_type, 'picking_type': picking.type })
            moves = [self._partial_move_for(cr, uid, m) for m in picking.move_lines if m.state not in ('done','cancel')]
            # chequeamos si es obligatoria la asignacion de lote
            if config and config.stock_production_lot:
                moves = [self._partial_move_for(cr, uid, m) for m in picking.move_lines if m.state not in ('done','cancel') and m.prodlot_id]
            # chequemos los moves por si habrá ubicaciones encadenadas
            for move in moves:
                if loc_obj.browse(cr, uid, move['location_dest_id']).chained_location_id:
                    move['location_dest_id'] = loc_obj.browse(cr, uid, move['location_dest_id']).chained_location_id.id
            res.update(move_ids=moves)
        return res

    def do_partial(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        super(inherit_stock_partial_picking, self).do_partial(cr, uid, ids, context)
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        purchase_obj = self.pool.get('purchase.order')
        uom_obj = self.pool.get('product.uom')
        partial_brw = self.browse(cr, uid, ids[0], context=context)
        picking_id = context.get('active_ids', [False])[0]
        wf_service = netsvc.LocalService("workflow")
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        origin = False
        new_picking = False
        new_picking_return = False
        return_move_ids = []
        partner_id = 1 # Wired: partner Herrera C.A.
        company_id = 1 # Wired: company Herrera C.A.
        if not picking_id:
            raise osv.except_osv(_('No se encontró albaran!'), _(
                                        '''Existe un error de integridad
                                        que impide leer el albarán!\n
                                        Por favor contacte a su administrador.''')
                                        )

        picking_brw = picking_obj.browse(cr, uid, picking_id, context = context)
        picking_type = context.get('default_type', False) or picking_brw.type
        purchase_id = picking_brw.purchase_id.id
        
        # albaranes de entrada (Compras)
        if picking_type == 'in' and purchase_id:
            #~ if not purchase_id:
                #~ raise osv.except_osv(_('No se encontró ODC!'), _(
                                            #~ '''Es necesario que los 
                                            #~ movimientos esten asociados 
                                            #~ a un pedido de compra!\n
                                            #~ Por favor verifique bien la 
                                            #~ informacion del albaran o 
                                            #~ contacte a su administrador.''')
                                            #~ )
            
            # actualizacion de reception_date y ref_sada
            picking_ids = picking_obj.search(cr, uid, [('purchase_id','=',purchase_id)])
            main_pick_id = min(picking_ids)
            main_pick_brw = picking_obj.browse(cr, uid, main_pick_id, context = context)
            main_pick_id = main_pick_brw.state == 'done' and main_pick_id or max(picking_ids)
            partial_vals = {'ref_sada' : partial_brw.ref_sada, 'reception_date': partial_brw.reception_date}
            picking_obj.write(cr, uid, [main_pick_id], partial_vals)
            
            # capturamos los valores para origin, partner y company
            purchase_brw = purchase_obj.browse(cr, uid, purchase_id, context=context)
            origin = purchase_brw.name + ((purchase_brw.origin and (':' + purchase_brw.origin)) or '')
            partner_id = purchase_brw.company_id.partner_id.id
            company_id = purchase_brw.company_id.id
        
        # validamos que no todos los movimientos sean devoluciones
        all_refund = [ x.id for x in partial_brw.move_ids if x.to_refund ]
        
        if not partial_brw.location_stock_id or len(partial_brw.move_ids) == len(all_refund) :
            return {'type': 'ir.actions.act_window_close'}
        
        # Mover la mercancia con destino ENTRADA en otra ubicacion almacenable 
        if partial_brw.move_ids and partial_brw.location_stock_id.id:
            seq_obj_name = 'stock.picking'
            transfer_type = 'internal'
            new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
            new_picking = picking_obj.create(cr, uid, {
                                        'name': new_pick_name,
                                        'date': date_cur,
                                        'partner_id': partner_id,
                                        'company_id': company_id,
                                        'transfer_type': transfer_type,
                                        'move_lines' : [],
                                    })
            # si origin tiene algun valor actualizamos el picking
            if origin:
                picking_obj.write(cr, uid, new_picking, { 'origin': origin } )
            
            # creamos los stock.move's de este picking
            for wizard_line in partial_brw.move_ids:
                # desplazamos solo los que no deben ser devueltos
                if not wizard_line.to_refund:
                    move_id = move_obj.create(cr,uid,{'name' : '[' + wizard_line.product_id.default_code + '] ' + wizard_line.product_id.name,
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uos_qty': wizard_line.quantity,                                        
                                                    'product_uom': wizard_line.product_uom.id,                                        
                                                    'product_uos': wizard_line.product_uom.id,                                        
                                                    'measure': wizard_line.measure,                                        
                                                    'prodlot_id': wizard_line.prodlot_id.id,                                        
                                                    'location_id' : wizard_line.location_dest_id.id,                                        
                                                    'location_dest_id' : partial_brw.location_stock_id.id,
                                                    'picking_id': new_picking
                                                    },context=context)
                else:
                    return_move_ids.append(wizard_line.move_id.id)
                    
            # si existen movimientos para devolucion creamos el picking
            if return_move_ids:
                seq_obj_name = 'stock.picking'
                new_type = 'internal'
                if picking_type =='out':
                    new_type = 'in'
                    seq_obj_name = 'stock.picking.in'
                elif picking_type =='in':
                    new_type = 'out'
                    seq_obj_name = 'stock.picking.out'
                new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
                new_picking_return = picking_obj.copy(cr, uid, picking_brw.id, {
                                                'name': _('%s-%s-return') % (new_pick_name, picking_brw.name),
                                                'move_lines': [], 
                                                'state':'draft', 
                                                'type': new_type,
                                                'date':date_cur, 
                })
                for move_id in return_move_ids:
                    move = move_obj.browse(cr, uid, move_id, context=context)
                    new_location = move.location_dest_id.id
                    returned_qty = move.product_qty
                    if returned_qty:
                        new_move=move_obj.copy(cr, uid, move_id, {
                                                    'product_qty': returned_qty,
                                                    'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, returned_qty, move.product_uos.id),
                                                    'picking_id': new_picking_return, 
                                                    'state': 'draft',
                                                    'location_id': new_location, 
                                                    'location_dest_id': move.location_id.id,
                                                    'prodlot_id': move.prodlot_id.id,
                                                    'date': date_cur,
                        })
                        move_obj.write(cr, uid, [move_id], {'move_history_ids2':[(4,new_move)]}, context=context)
                    
        if new_picking:
            # confirmamos el picking
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
            # luego lo finalizamos 
            picking_obj.action_move(cr, uid, [new_picking], context=context)
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
            
        if new_picking_return:
            # confirmamos el picking return
            wf_service.trg_validate(uid, 'stock.picking', new_picking_return, 'button_confirm', cr)
            # luego lo finalizamos 
            picking_obj.action_move(cr, uid, [new_picking_return], context=context)
            wf_service.trg_validate(uid, 'stock.picking', new_picking_return, 'button_done', cr)
                
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'reception_date': fields.datetime('Fecha de Recepción', help = "Fecha de Recepción de la Mercancía"),
        'ref_sada': fields.char('Guia SADA', size = 8, help = "Número de Guia SADA para la recepción"),
        'transfer_type': fields.char('Transfer Type', size = 16, help = "Indica si la transferencia es dentro de la sucursal o entre sucursales"),
        'picking_type': fields.char('Picking Type', size = 16, help = "Tipo de picking: entrada, salida o interno"),
        'location_stock_id': fields.many2one('stock.location', 'Ubicación de almacenamiento', help="Location where the system will stock the finished products."),
        'location_list' : fields.function(_get_locations, type='char', string='Lista', store=False, method=False, help='partners are only allowed to be withholding agents'),
    }

    _defaults = {
        'reception_date': str(datetime.datetime.today()),
    }

    _constraints = [(_check_date, 'La fecha ingresada debe ser menor a la fecha actual',['reception_date'])]

inherit_stock_partial_picking()

class stock_partial_picking_line(osv.TransientModel):
    _inherit = "stock.partial.picking.line"

    _columns = {
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
        'to_refund':fields.boolean('Devolver', help= "Marcar para ser devuelta al proveedor"),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        res = super(stock_partial_picking_line,self).onchange_product_id(cr, uid, ids, product_id, context=context)
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            measure = product.measure_po or product.measure
            res['value'].update({'measure': measure})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
