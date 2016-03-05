# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime

class wizard_distribution_line_picking(osv.osv_memory):
    _name = "wizard.distribution.line.picking"

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(wizard_distribution_line_picking, self).default_get(cr, uid, fields_list, context)
        ids = context['active_ids']
        if ids:
            wLines = []
            dLine_brw = self.pool.get('stock.distribution.line').browse(cr, uid, ids[0], context)
            pick = dLine_brw.picking_id or False
            if not pick:
                raise osv.except_osv(_('Advertencia!!!'), _(u'No hay albarán realacionado a este pedido, consulte con su Administrador!'))
            for move in pick.move_lines:
                wizardLine = {
                        'move_id' : move.id,
                        'product_id' : move.product_id.id,
                        'product_qty' : move.product_qty,
                        'prodlot_id' : move.prodlot_id and move.prodlot_id.id or '',
                        'location_dest_id' : move.location_dest_id.id,
                        'confirm' : move.distribution_confirm,
                        }
                wLines.append((0,0,wizardLine))
            if wLines:
                res.update({
                         'name': dLine_brw.picking_id.sale_id.name,
                         'picking_id': dLine_brw.picking_id.id, 
                         'line_ids': wLines
                })
        return res

    def confirm_and_save(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        wzd_brw = self.browse(cr, uid, ids[0], context)
        for wLine in wzd_brw.line_ids:
            move_obj.write(cr, uid, wLine.move_id.id, {'distribution_confirm': wLine.confirm })
        return True
        
    def action_ok_all(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        wzd_brw = self.browse(cr, uid, ids[0], context)
        for wLine in wzd_brw.line_ids:
            move_obj.write(cr, uid, wLine.move_id.id, {'distribution_confirm': True })
        return True

    _columns = {
        'name' : fields.char('Pedido de venta', size = 10, required = True),
        'picking_id' : fields.many2one('stock.picking', 'Albarán relacionado'),
        'line_ids': fields.one2many('wizard.distribution.line.move', 'parent_id', 'Líneas'),
    }

wizard_distribution_line_picking()

class wizard_distribution_line_move(osv.osv_memory):
    _name = "wizard.distribution.line.move"

    _columns = {
            'parent_id' : fields.many2one('wizard.distribution.line.picking', 'Encabezado'),
            'move_id' : fields.many2one('stock.move', 'Movimiento de Stock'),
            'product_id' : fields.many2one('product.product', 'Producto'),
            'product_qty': fields.float('UdV'),
            'prodlot_id' : fields.many2one('stock.production.lot', 'Número de Lote'),
            'location_dest_id' : fields.many2one('stock.location', 'Ubicación Destino'),
            'confirm': fields.boolean('Confirmar'),
    }
    
    _defaults = {
        'confirm': False,
    }

wizard_distribution_line_move()




