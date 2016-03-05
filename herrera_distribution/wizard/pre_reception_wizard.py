# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp import netsvc
import time

class pre_reception_wizard(osv.osv_memory):
    _name = "pre.reception.wizard"

    def default_get(self, cr, uid, fields_list, context=None):
	context = context and context or {}
        res = super(pre_reception_wizard, self).default_get(cr, uid, fields_list, context)
        distribution_id = context['active_id']
        invoices = []
        if distribution_id:
            for line in self.pool.get('stock.distribution').browse(cr, uid, distribution_id, context).line_ids:
		for invoice in line.sale_id.invoice_ids:
		    if invoice.state == 'open':
			inv = {
			    'number' : invoice.number,
			    'nro_ctrl' : invoice.nro_ctrl,
			    'partner_id': invoice.partner_id.id,
			    'origin': invoice.origin,
			    'amount_total' : invoice.amount_total,
			    'picking_id': line.picking_id.id,
			    'invoice_id': invoice.id,
			    }
			invoices.append((0,0,inv))
		    else:
			raise osv.except_osv(_('Error!'), _('La Factura de %s, con monto %s, aun no posee Numero Interno, por favor valide la factura!!!'%(invoice.partner_id.name, invoice.amount_total)) )
            if invoices:
                res.update({'distribution_id': distribution_id, 'invoice_ids': invoices})
        return res

    def create_reception(self, cr, uid, ids, context=None):
	context = context and context or {}
	wzd = self.browse(cr, uid, ids[0], context)
	invoice_obj = self.pool.get('account.invoice')
	invoice_ids = []
	for wzd_line in wzd.invoice_ids:
	    invoice_id = wzd_line.invoice_id.id
	    invoice_obj.write(cr, uid, [invoice_id], {'reception_type': wzd_line.reception_type,
							'reception_progress': 'draft',
							'date_document': wzd_line.date_document
							})
	    invoice_ids.append(invoice_id)
	reception_id = self.pool.get('stock.reception').create(cr, uid, {
							    'distribution_id': wzd.distribution_id.id,
							    'name': wzd.distribution_id.name,
							    'shop_id': wzd.distribution_id.shop_id.id,
							    'invoice_ids': [(6,0,invoice_ids)],
							})
	if not reception_id:
	    raise osv.except_osv(_('Error!'), _('Error al crear la Pre-Recepcion!!!' ))
	self.pool.get('stock.distribution').write(cr, uid, [wzd.distribution_id.id], {'state': 'pre-reception'})
	tree_obj_id = self.pool.get('ir.model.data').search(cr,uid,[('name','=','stock_reception_tree')])
        tree_res_id = self.pool.get('ir.model.data').browse(cr,uid,tree_obj_id[0]).res_id
        return {
           'name': 'Recepción',
           'view_type': 'form',
           'view_mode': 'form,tree',
           'views': [(tree_res_id,'tree')],
           'res_model': 'stock.reception',
           'type': 'ir.actions.act_window'
        }

    _columns = {
		'distribution_id': fields.many2one('stock.distribution', "Despacho"),
		'invoice_ids': fields.one2many('pre.reception.wizard.line','parent_id',"Seleccione un Despacho"),
    }

pre_reception_wizard()

class pre_reception_wizard_line(osv.osv_memory):
    _name = "pre.reception.wizard.line"

    _columns = {
	    'parent_id': fields.many2one('pre.reception.wizard', 'Encabezado'),
	    'picking_id': fields.many2one('stock.picking', 'Albarán Asociados'),
	    'invoice_id': fields.many2one('account.invoice', 'Factura'),
            'number': fields.char("Número de Factura"),
	    'partner_id': fields.many2one('res.partner', 'Cliente', help = 'Cliente'),
	    'nro_ctrl': fields.char("Número de Control"),
	    'origin': fields.char("Origen"),
	    'amount_total' : fields.float("Monto"),
	    'date_document' : fields.date("Fecha de Recepción", help="Fecha de recepción por parte del cliente"),
	    'reception_type' : fields.selection([
				    ('received', 'Entregada'),
				    ('rejected', 'Rechazada'),
				    ('resent', 'Reenvio'),
				    ('partial_refund', 'N.C. Parcial'),
				    ], 'Tipo de Recepción', select=True),
    }

pre_reception_wizard_line()
