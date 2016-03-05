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

class invoice_control_number(osv.osv_memory):

    _name = 'invoice.control.number'

    def default_get(self, cr, uid, fields_list, context = None):
        context = context and context or {}
        res = super(invoice_control_number, self).default_get(cr, uid, fields_list, context)
        ctx_lines = context.get('lines',False) and context['lines'] or False
        ctx_reopen = context.get('reopen',False)
        ctx_origin = context.get('origin',False)
        if ctx_origin:
            res.update({'origin':ctx_origin})
        if ctx_lines:
            res.update({'line_ids': ctx_lines,'ok':True,'reopen':ctx_reopen})
        else:
            ids = context['active_ids']
            lines = []
            if ids:
                for invoice_brw in self.pool.get('account.invoice').browse(cr, uid, ids, context):
                    invoice_type = unicodedata.normalize('NFKD', invoice_brw.type).encode('ascii','ignore')
                    if invoice_type != 'out_invoice':
                        raise osv.except_osv(_('Error!'), _('Este proceso se aplica solo a Facturas de Cliente!'))
                    if invoice_brw.invoice_lot_id:
                        raise osv.except_osv(_('Error!'), _('La factura %s ya está asignada al lote %s!'%(invoice_brw.number,invoice_brw.invoice_lot_id.name)))
                    line = {
                            'partner_id': invoice_brw.partner_id and invoice_brw.partner_id.id or '',
                            'origin': invoice_brw.origin or '',
                            'amount_total': invoice_brw.amount_total or 0.0,
                            'invoice_id': invoice_brw.id,
                    }
                    lines.append((0,0,line))
                if lines:
                    res.update({'line_ids': lines})
        return res

    def check_string(self, cr, uid, string, context = None):
        context = context and context or {}
        if not string:
            raise osv.except_osv(_('Error!'), _('Ingrese un Número Inicial!'))
            return False
        if len(string) < 11:
            raise osv.except_osv(_('Error!'), _('Cantidad de cifras no es válida!'))
            return False
        if not string[0:3] == '00-' or string[3:11].isdigit() is False:
            raise osv.except_osv(_('Error!'), _('Formato del Número no es Válido!'))
            return False
        if not len(string[3:12]) == 8:
            raise osv.except_osv(_('Error!'), _('Cantidad de cifras no es válida!'))
            return False
        if self.pool.get('account.invoice').search(cr, uid, [('nro_ctrl','=',string)]):
            raise osv.except_osv(_('Error!'), _('Número de control ya existe!'))
            return False
        return True

    def set_control_number(self, cr, uid, ids, context = None):
        context = context and context or {}
        wzd = self.browse(cr, uid, ids[0], context)
        initial = wzd.initial
        reopen = wzd.reopen
        origin = wzd.origin
        context.update({'initial':initial,'reopen':reopen,'origin':origin})
        lines= []
        if self.check_string(cr, uid, initial, context):
            number = int(initial.split('-')[1])
            for wzd_line in wzd.line_ids:
                nro_ctrl = initial[0:3]+str(number).zfill(8)
                line = {
                            'invoice_id': wzd_line.invoice_id.id,
                            'partner_id': wzd_line.partner_id.id,
                            'origin': wzd_line.origin,
                            'amount_total': wzd_line.amount_total,
                            'nro_ctrl': nro_ctrl,
                        }
                lines.append((0,0,line))
                number+=1
            context.update({'lines':lines})
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

    def write_invoice(self, cr, uid, ids, context = None):
        context = context and context or {}
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = []
        invoice_lot = []
        wzd = self.browse(cr, uid, ids[0], context)
        wf_service = netsvc.LocalService('workflow')
        if not wzd.sure:
            raise osv.except_osv(_('Ejecución inválida!'),_('Debe tildar "Esta usted seguro?" para continuar'))
        if not context.get('lines',False):
            raise osv.except_osv(_('Ejecución inválida!'),_('No has ingresado un número inicial para asignar a la serie'))
        for wzd_line in wzd.line_ids:
            if wzd_line.nro_ctrl:
                vals = {'nro_ctrl': wzd_line.nro_ctrl}
                if context.get('reopen',False):
                    vals.update({'print_state':'reopen'})
                invoice_id = wzd_line.invoice_id.id
                invoice_obj.write(cr, uid, [invoice_id], vals)
                if wzd.validate_invoice:
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                 # si no esta asociada a un lote
                if not wzd_line.invoice_id.invoice_lot_id:
                    invoice_ids.append(invoice_id)
        if invoice_ids:
            invoice_lot = self.pool.get('account.invoice.lot')
            invoice_lot.create(cr, uid, {
                                            'name': self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.lot'),
                                            'initial': context['initial'],
                                            'state': 'open',
                                            'date_open': time.strftime('%Y-%m-%d'),
                                            'invoice_ids': [(6,0,invoice_ids)],
                                            'origin': wzd.origin,
                                        })
        return {'type': 'ir.actions.act_window_close'}

    def print_invoice(self, cr, uid, ids, context = None):
        invoice_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService('workflow')
        wzd = self.browse(cr, uid, ids[0], context)
        invoice_ids = []
        # Modificamos las facturas
        res = self.write_invoice(cr, uid, ids, context=context)
        # Ubicamos los ids de las facturas para generar el reporte
        for wzd_line in wzd.line_ids:
            if wzd_line.nro_ctrl:
                invoice_id = wzd_line.invoice_id.id
                invoice_obj.write(cr, uid, [invoice_id], {'nro_ctrl': wzd_line.nro_ctrl})
                invoice_ids.append(invoice_id)
                if wzd.validate_invoice:
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
        if invoice_ids:
            res = {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.invoice',
                'datas': {
                     'ids': invoice_ids,
                     'model': 'account.invoice',
                     'form': invoice_obj.read(cr, uid, invoice_ids, context=context)
                },
                'nodestroy' : True
            }
        return res

    _columns = {
        'sure' :fields.boolean('Seguro?'),
        'ok':fields.boolean('Continuar'),
        'validate_invoice' :fields.boolean('Válidar Facturas?', help="El proceso validará el lote de facturas automaticamente mostradas en este asistente"),
        'initial': fields.char('Número Inicial', size=11, help="Número por el cual comienza la serie"),
        'line_ids' : fields.one2many('invoice.control.number.line', 'parent_id', 'Facturas'),
        'reopen' : fields.boolean('Re-apertura de lote'),
        'origin' : fields.char('Origen', size=11, help="Procedencia del lote"),
    }

    _defaults = {
        'validate_invoice': True,
        'ok': False,
    }

invoice_control_number()

class invoice_control_number_line(osv.osv_memory):

    _name = 'invoice.control.number.line'

    _columns = {
        'parent_id': fields.many2one('invoice.control.number', 'Wizard Padre'),
        'invoice_id': fields.many2one('account.invoice', 'Factura'),
        'partner_id': fields.many2one('res.partner', 'Cliente', help = 'Cliente'),
        'origin': fields.char('Origen', help = 'Pedido de Ventas Asociado'),
        'nro_ctrl': fields.char('Número de Control'),
        'amount_total': fields.float('Monto Total'),
    }

invoice_control_number_line()
