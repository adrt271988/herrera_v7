# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
import openerp.addons.decimal_precision as dp
import openerp.exceptions
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

def str_to_datetime(strdate):
    return datetime.datetime.strptime(strdate, tools.DEFAULT_SERVER_DATE_FORMAT)

class account_invoice_lot(osv.osv):
    '''Lotes de facturas para Herrera C.A. '''
    _name = "account.invoice.lot"

    def invoice_print(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Esta opción sólo se puede ser usada para un sólo lote a la vez.'
        # Declaracion de variables
        inv_lot = self.browse(cr, uid, ids[0], context=context)
        invoice_ids = map(lambda x: x.id, inv_lot.invoice_ids)
        # Evaluamos si el proceso debe continuar
        if not invoice_ids:
            raise osv.except_osv(_('Acción inválida!'), _('No se encontraron facturas en este lote'))
        if not inv_lot.state == 'open':
            raise osv.except_osv(_('Acción inválida!'), _('Ya este lote está cerrado, para volver a imprimir las facturas contacte al administrador de la sucursal!'))
        # Actualizamos el estado de impresion de las facturas
        self.pool.get('account.invoice').set_print_state(cr, uid, 
                        invoice_ids, context=context)
        # Cerramos el lote
        self.write(cr, uid, ids, { 
                        'date_close': time.strftime('%Y-%m-%d %H:%M:%S')
                        }, context=context)
        # Preparamos la data para abrir el pdf
        datas = {
             'ids': invoice_ids,
             'model': 'account.invoice',
             'form': self.pool.get('account.invoice').read(cr, uid, 
                        invoice_ids, context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice',
            'datas': datas,
            'nodestroy' : True
        }
        
    def _get_lot_state(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method update the invoice lot state taking into account
        invoice the print state.
        """
        context = context or {}
        res = {}.fromkeys(ids, 'open')
        for lot_brw in self.browse(cr, uid, ids, context=context):
            close = all([x.print_state in ['printed','reprinted'] for x in lot_brw.invoice_ids])
            if close:
                res[lot_brw.id] = 'close'
        return res

    def _get_lot_id_to_update(self, cr, uid, ids, context=None):
        """
        @param ids: account invoices ids list.
        @return: a list of Work Order Lots who Work Workorders state have been
        change.
        """
        context = context or {}
        invoice_obj = self.pool.get('account.invoice')
        res = [brw.invoice_lot_id.id
               for brw in invoice_obj.browse(cr, uid, ids, context=context)]
        res = list(set(res))
        return res
    
    def _get_initial_number(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method update the invoice lot state taking into account
        invoice the print state.
        """
        context = context or {}
        initial = 99999999
        res = {}
        for lot_brw in self.browse(cr, uid, ids, context=context):
            for inv_brw in lot_brw.invoice_ids:
                if int(inv_brw.nro_ctrl[3:]) < initial:
                    initial = int(inv_brw.nro_ctrl[3:])
            res[lot_brw.id] = '00-'+str(initial).zfill(8)
        return res
    
    def _count_done(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method update the invoice lot state taking into account
        invoice the print state.
        """
        context = context or {}
        res = {}.fromkeys(ids, 0)
        for lot_brw in self.browse(cr, uid, ids, context=context):
            res[lot_brw.id] = len([ x for x in lot_brw.invoice_ids if x.print_state in ['printed','reprinted']])
        return res

    def _count_wait(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method update the invoice lot state taking into account
        invoice the print state.
        """
        context = context or {}
        res = {}.fromkeys(ids, 0)
        for lot_brw in self.browse(cr, uid, ids, context=context):
            res[lot_brw.id] = len([ x for x in lot_brw.invoice_ids if x.print_state not in ['printed','reprinted']])
        return res
        
    _columns = {
            'name': fields.char('Código', size=10, help="Código de identificación del Lote"),
            'initial': fields.function(_get_initial_number, type='char',
            size=11, string="Inicio de serie", store={ 
                'account.invoice.lot': (lambda self, cr, uid, ids, c={}: ids, ['invoice_ids'], 10),
                'account.invoice':(_get_lot_id_to_update, ['nro_ctrl'], 10) 
            }, 
            help="Número de inicio del Lote"),
            'count_done': fields.function(_count_done, type='integer',
            string="Facturas impresas", help="Facturas del lote que han sido impresa"),
            'count_wait': fields.function(_count_wait, type='integer',
            string="Facturas sin imprimir", help="Facturas del lote por imprimir"),
            'invoice_ids' : fields.one2many('account.invoice', 'invoice_lot_id', 'Facturas Asociadas al Lote'),
            'date_open': fields.date('Fecha de Apertura'),
            'date_close': fields.date('Fecha de Cierre'),
            'state': fields.function(
            _get_lot_state,
            type='selection',
            string='Estado',
            selection=[('open', 'Abierto'),
                       ('close', 'Cerrado')],
            required=True,
            store={'account.invoice':
                   (_get_lot_id_to_update, ['print_state'], 10)},
            help='Indicate the state of the Lot.'),
            'origin' : fields.char('Origen', size=11, help="Procedencia del lote"),
    }

    _defaults = {
        'state': 'open',
    }

account_invoice_lot()
