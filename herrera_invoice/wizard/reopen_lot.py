# -*- encoding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
from openerp.tools.float_utils import float_compare
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
import unicodedata

class reopen_account_invoice_lot(osv.osv_memory):

    _name = 'reopen.account.invoice.lot'

    def default_get(self, cr, uid, fields_list, context=None):
        context = context and context or {}
        res = super(reopen_account_invoice_lot, self).default_get(cr, uid, fields_list, context)
        lines = []
        invoice_lot_id = 'active_id' in context and context['active_id']
        if not context.get('active_model',False)=='account.invoice.lot':
            raise osv.except_osv(_('Acción Invalida!'), _('Debe ejecutar esta acción desde el módulo "Lotes de Facturas"'))
        if not invoice_lot_id:
            raise osv.except_osv(_('Error de lectura!'), _('No se pudo cargar la informacion del lote'))
        invoice_brw = self.pool.get('account.invoice.lot').browse(cr, 
                    uid, invoice_lot_id, context=context).invoice_ids
        for invoice in invoice_brw:
            invoice_type = unicodedata.normalize('NFKD', invoice.type).encode('ascii','ignore')
            if invoice_type != 'out_invoice':
                raise osv.except_osv(_('Error!'), _('Este proceso se aplica solo a Facturas de Cliente!'))
            line = {
                    'partner': invoice.partner_id and invoice.partner_id.name or '',
                    'origin': invoice.origin or '',
                    'nro_ctrl': invoice.nro_ctrl,
                    'amount_total': invoice.amount_total or 0.0,
                    'invoice_id': invoice.id,
            }
            lines.append((0,0,line))
        if lines:
            res.update({'select_lines': lines})
        return res

    def action_reopen(self, cr, uid, ids, context=None):
        context = context and context or {}
        invoice_obj = self.pool.get('account.invoice')
        wzd = self.browse(cr, uid, ids[0], context)
        select_mode = wzd.select_mode
        lines = []
        wzd_lines = select_mode == 'all' and wzd.select_lines or \
        [ x for x in wzd.select_lines if x.reopen ]
        for wzd_line in wzd_lines:
            line = {
                'invoice_id': wzd_line.invoice_id.id,
                'partner_id': wzd_line.invoice_id.partner_id.id,
                'origin': wzd_line.origin,
                'amount_total': wzd_line.amount_total,
            }
            lines.append((0,0,line))
        if lines:
            context.update({'lines':lines,'reopen': True})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','invoice_control_number_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.control.number',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
        
    _columns = {
        'select_mode' : fields.selection([
                ('all','Todas'),
                ('custom','Seleccionar'),], 'Facturas', required=True),
        'select_lines' : fields.one2many('reopen.account.invoice.lot.line', 'parent_id', 'Facturas'),
    }

    _defaults = {
        'select_mode': 'all',
    }

reopen_account_invoice_lot()

class reopen_account_invoice_lot_line(osv.osv_memory):

    _name = 'reopen.account.invoice.lot.line'

    _columns = {
        'parent_id': fields.many2one('reopen.account.invoice.lot', 'Wizard Padre'),
        'invoice_id': fields.many2one('account.invoice', 'Número de factura'),
        'partner': fields.char('Cliente', size=128),
        'origin': fields.char('Origen', help = 'Pedido de Ventas Asociado'),
        'nro_ctrl': fields.char('Número de control'),
        'amount_total': fields.float('Total'),
        'reopen': fields.boolean('Reabrir'),
    }
    
    _defaults = {
        'reopen': False,
    }

reopen_account_invoice_lot_line()
