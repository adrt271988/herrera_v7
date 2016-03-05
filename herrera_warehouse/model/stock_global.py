# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp import netsvc
from datetime import datetime
import time
from openerp.tools import float_compare

class stock_global(osv.osv):
    _name = "stock.global"
    _order = "date desc"

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for g in self.browse(cr, uid, ids, context=context):
            if g.state == 'confirmed':
                raise osv.except_osv(_('Warning!'), _('No es posible eliminar el documento una vez que ya está confirmado!!!') )
        return super(stock_global, self).unlink(cr, uid, ids, context=context)

    def action_ok_all(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        global_brw = self.browse(cr, uid, ids[0], context=context)
        if global_brw.state == 'draft':
            for line in global_brw.global_lines:
                line.write({'ok':True})
        return {'type':'ir.actions.act_window_close', 'auto_refresh':'1' }

    def set_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True
    
    def set_confirm(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        
        if context is None:
            context = {}
        
        pickings = []
        complete = []
        ctx = dict(context, active_model=self._name, active_ids=ids, active_id=ids[0])
        global_brw = self.browse(cr, uid, ids[0], context)
        # Recorremos todos los moves asociados a la global
        for line in global_brw.global_lines:
            real_qty = line.real_qty
            # Validamos que no haya cantidades reales en 0 (cero)
            if real_qty < 0:
                raise osv.except_osv(_('Advertencia!'), _('No puede ingresar una valor negativo! Modifique cantidad real para %s'%line.name) )
            # Validamos que la cantidad real no sea mayor a la virtual
            if real_qty > line.product_qty:
                raise osv.except_osv(_('Advertencia!'), _('La cantidad real ingresada para %s no puede ser mayor a la cantidad en pedidos!'%line.name) )
            # Validamos que la cantidad real no sea mayor a la virtual
            if not line.ok:
                raise osv.except_osv(_('Advertencia!'), _('Debe confirmar todas la lineas para poder confirmar la global!'))
            for move in line.move_ids:
                if move.picking_id.id not in pickings:
                    pickings.append(move.picking_id.id)
                move_qty = move.product_qty
                # Mientras haya cantidad real hacemos 'Done' los stock.move
                #~ print 'move %s %f'%(move.id,real_qty)
                if real_qty > 0.0:
                    # Se deduce la cantidad real por cada stock.move
                    if real_qty >= move_qty:
                        real_qty -= move_qty
                        #~ move_obj.action_done(cr, uid, [move.id], context)
                    # Si la cantidad real es insuficiente
                    else:
                        # El restante de la cantidad real se hace 'done'
                        done_qty = real_qty
                        # Se prepara la cantidad a ser cancelada
                        cancel_qty = move_qty - real_qty
                        # La cantidad real se consume completamente
                        real_qty = 0.0
                        # Se actualiza la cantidad antes de hacer 'done'
                        move_obj.write(cr, uid, [move.id], {'product_qty':done_qty}, context)
                        # 'Done' al stock.move
                        #~ move_obj.action_done(cr, uid, [move.id], context)
                        # Se crea un stock.move para cancelar la cantidad que no pudo ser consumida
                        move_to_cancel = move_obj.create(cr,uid,{'name' : '[' + move.product_id.default_code + '] ' + move.product_id.name,
                                        'product_id': move.product_id.id,
                                        'product_qty': cancel_qty,
                                        'product_uom': move.product_uom.id,
                                        'prodlot_id': move.prodlot_id.id,
                                        'measure': move.product_id.measure,
                                        'location_id' : move.location_id.id,
                                        'location_dest_id' : move.location_dest_id.id,
                                        'picking_id': move.picking_id.id,
                                        },context=context)
                        # Se cancela el movimiento
                        move_obj.action_cancel(cr, uid, [move_to_cancel], context)
                    # Incorporamos el move a la lista de completados
                    complete.append(move)
                # Cuando se agota la cantidad real cancelamos el stock.move
                else:
                    move_obj.action_cancel(cr, uid, [move.id], context)

        # Se cancelan los moves que no estan en la lista de completados
        for picking in picking_obj.browse(cr, uid, pickings, context=context):
            for move in picking.move_lines:
                if move not in complete:
                    move_obj.action_cancel(cr, uid, [move.id], context)

        # Hacemos 'Done' a todos los moves de la lista de completados
        for move in complete:
            move_obj.action_done(cr, uid, [move.id], context=context)
            if move.picking_id.id :
                # TOCHECK : Done picking if all moves are done or cancel
                cr.execute("""
                    SELECT move.id FROM stock_picking pick
                    RIGHT JOIN stock_move move ON move.picking_id = pick.id AND move.state in %s
                    WHERE pick.id = %s""",
                            (tuple(['done','cancel']), move.picking_id.id))
                res = cr.fetchall()
                if len(res) == len(move.picking_id.move_lines):
                    picking_obj.action_move(cr, uid, [move.picking_id.id], context=context)
                    # Haciendo 'Done' el picking se dispara una accion que 
                    # crea un nuevo picking con destino a la ubicacion encadenada
                    wf_service.trg_validate(uid, 'stock.picking', move.picking_id.id, 'button_done', cr)
        
        self.write(cr, uid, ids, {'state': 'confirmed'})
        #~ self.do_partial(cr, uid, ids[0], pickings, context)
        return True
    
    _columns = {
        'name' : fields.char('Número de Global', size = 10, required = True),
        'state':fields.selection([
            ('draft', 'Esperando confirmación'),
            ('confirmed', 'Confirmada'),
            ('cancel', 'Cancelada'),
            ], 'Status', select=True),
        'date': fields.datetime('Fecha', required=True),
        'global_lines' : fields.one2many('stock.global.line', 'global_id', 'Items de Global'),
    }

    _defaults = {
        'state': 'draft',
        'date': fields.date.context_today,
    }

stock_global()

class stock_global_line(osv.osv):
    _name = "stock.global.line"

    _columns = {
        'name': fields.char('Descripcion', size=128, required=True), 
        'item' : fields.char('N°', size = 3),
        'product_id': fields.many2one('product.product', 'Producto', help = 'Producto'),
        'uom_id': fields.many2one('product.uom', 'Unidad de Medida', help = 'Unidad de Medida'),
        'global_id': fields.many2one('stock.global', 'Global'),
        'product_qty' : fields.float("Cantidad", help = 'Cantidad del producto en Unidades de Venta'),
        'weight' : fields.float("Peso (Kgs)", help = 'Peso en Kilogramos'),
        'volume' : fields.float("Volumen", help = 'Volumen en m3'),
        'supplier_code' : fields.char("Código de Producto", help = 'Codigo de Producto dado por el Proveedor'),
        'palette' : fields.char("N° de Paletas", help = 'Cantidad de Paletas que representan las unidades de ventas'),
        'move_ids': fields.one2many('stock.move', 'gline_id', 'Picking Asociados'),
        'real_qty': fields.float("Cantidad Real", help="Existencia real en el inventario"), 
        'ok': fields.boolean('Confirmado', help="Confirmar si la cantidad a despachar ha sido comprobada en el inventario"),
    }
    
    _defaults = {
        'ok': False,
    }

stock_global_line()

class stock_hall_document(osv.osv):
    _name = "stock.hall.document"

    _columns = {
        'name' : fields.char('Número de Listin', size = 10),
        'date': fields.datetime('Fecha'),
        'global_id': fields.many2one('stock.global', 'Global'),
        'hall': fields.char('Pasillo'),
        'lines': fields.one2many('stock.hall.document.line', 'hall_id', 'Items de Listín'),
    }

stock_hall_document()


class stock_hall_document_line(osv.osv):
    _name = "stock.hall.document.line"

    _columns = {
        'name' : fields.char('Item', size = 3),
        'product_id': fields.many2one('product.product', 'Producto', help = 'Producto'),
        'prodlot_id': fields.many2one('stock.production.lot', 'N° de Serie', help = 'Producto'),
        'hall_id': fields.many2one('stock.hall.document', 'Listín'),
        'uom_id': fields.many2one('product.uom', 'Unidad de Medida', help = 'Unidad de Medida'),
        'location_id': fields.many2one('stock.location', 'Ubicación'),
        'product_qty' : fields.float("Cantidad", help = 'Cantidad del producto en Unidades de Venta'),
        'supplier_code' : fields.char("Código de Producto", help = 'Codigo de Producto dado por el Proveedor'),
        'palette' : fields.char("N° de Paletas", help = 'Cantidad de Paletas que representan las unidades de ventas'),
    }

stock_hall_document_line()
