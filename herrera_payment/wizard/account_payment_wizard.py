# -*- coding: utf-8 -*-
import openerp.netsvc as netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
import time

class account_payment_wizard(osv.osv_memory):
    _name = "account.payment.wizard"

    def create_account_moves(self, cr, uid, ids, invoice_id, debit_account_id, credit_account_id, partner_id, journal_id, inv_number, amount, period_id, date, vref, context):
        context = context and context or {}
        move_pool = self.pool.get('account.move')
        journal_code = self.pool.get('account.journal').browse(cr, uid, journal_id).code
        ref = journal_code+'/'+vref
        debit_line = {'name': '/','ref': inv_number,'account_id':debit_account_id,'debit':amount,'credit':0.00,'period_id': period_id,
                    'journal_id': journal_id,'partner_id': partner_id,'date': date}
        credit_line = {'name': inv_number,'ref': inv_number,'account_id':credit_account_id,'debit':0.00,'credit':amount,'period_id': period_id,
                    'journal_id': journal_id,'partner_id': partner_id,'date': date}
        lines = [(0,0,debit_line),(0,0,credit_line)]
        move_id = move_pool.create(cr, uid, {
                            'name': ref,
                            'date': date,
                            'ref': vref,
                            'period_id': period_id,
                            'journal_id': journal_id,
                            'line_id': lines,
                            })
        move_pool.button_validate(cr, uid, [move_id], context=context)
        return True

    def default_get(self, cr, uid, fields_list, context=None):
        context = context and context or {}
        res = super(account_payment_wizard, self).default_get(cr, uid, fields_list, context)
        if context:
            invoice_id = context['active_id']
            invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
            partner_id = context.get('partner_id') and context['partner_id'] or invoice.partner_id.id
            res.update({'partner_id': partner_id, 'invoice_id': invoice_id, 'amount': invoice.amount_total})
        return res

    def process_payment(self, cr, uid, ids, context=None):
        context = context and context or {}
        invoice = self.pool.get('account.invoice').browse(cr, uid, context['active_id'], context)
        context.update({'invoice_id':invoice.id}) ### llave utilizada en funcion recompute_voucher_lines
        wizard = self.browse(cr, uid, ids[0], context)
        voucher_pool = self.pool.get('account.voucher')
        vouchers = []
        total_vouchers = sum(map(lambda x : x.amount, wizard.voucher_ids))
        journal_types = map(lambda x : x.journal_id.type, wizard.voucher_ids)
        journal_wh = [j for j in journal_types if j in ('iva_sale','iva_purchase')]
        journal_mun = [j for j in journal_types if j in ('mun_sale','mun_purchase')]
        journal_islr = [j for j in journal_types if j in ('islr_sale','islr_purchase')]
        journal_dpp = [j for j in journal_types if j in ('sale_dpp')]
        if len(journal_wh) > 1 or len(journal_mun) > 1 or len(journal_islr) > 1 or len(journal_islr) > 1 or len(journal_dpp) > 1:
            raise osv.except_osv(_('Error!'), _('Existen dos retenciones por un mismo concepto!'))
        if total_vouchers > wizard.amount:
            raise osv.except_osv(_('Error!'), _('La suma de los instrumentos excede el monto de la factura!'))
        if not wizard.voucher_ids:
            raise osv.except_osv(_('Error!'), _('No ha ingresado ningún instrumento de pago!'))
        for voucher in wizard.voucher_ids:
            if voucher.journal_id.type == 'sale_dpp':
                recovery_pct = float(voucher.amount*100)/float(wizard.amount)
                iva_recovery = round(float(invoice.amount_tax*(recovery_pct/100)),2)
                rec_journal_id = self.pool.get('account.journal').search(cr, uid, [('type','=','dpp_recovery')])[0]
                self.create_account_moves(cr, uid, ids, invoice.id, voucher.account_id.id, invoice.account_id.id,\
                                wizard.partner_id.id, rec_journal_id, invoice.number,\
                                voucher.amount, voucher.period_id.id, voucher.date, voucher.reference, context = context)
            vals = voucher_pool.recompute_voucher_lines(cr, uid, [voucher.id], wizard.partner_id.id, voucher.journal_id.id, voucher.amount, invoice.currency_id.id, 'sale', voucher.date, context=context)
            voucher_lines = voucher_pool.recompute_payment_rate(cr, uid, [voucher.id], vals, invoice.currency_id.id, voucher.date, 'sale', voucher.journal_id.id, voucher.amount, context=context)
            drs = []
            crs = []
            for d in voucher_lines['value']['line_dr_ids']:
                drs.append((0,0,d))
            for c in voucher_lines['value']['line_cr_ids']:
                crs.append((0,0,c))
                vid = voucher_pool.create(cr, uid, {
                                    'reference': voucher.reference and voucher.reference or '',
                                    'date': voucher.date,
                                    'partner_id': wizard.partner_id.id,
                                    'pay_now': 'pay_now',
                                    'company_id': 1,
                                    'state': 'draft',
                                    'type': 'receipt',
                                    'payment_option': 'without_writeoff',
                                    'account_id': voucher.account_id.id,
                                    'period_id': voucher.period_id.id,
                                    'active': True,
                                    'line_dr_ids': drs,
                                    'line_cr_ids': crs,
                                    'journal_id': voucher.journal_id.id,
                                    'amount': voucher.amount,
                                    'partner_bank_id': voucher.partner_bank_id and voucher.partner_bank_id.id or ''
                                })
                vouchers.append(vid)
        voucher_pool.button_proforma_voucher(cr, uid, vouchers, context=context)
        return True

    _columns = {
            'invoice_id' : fields.many2one('account.invoice', 'Factura a Pagar'),
            'partner_id' : fields.many2one('res.partner', 'Cliente'),
	    'amount' : fields.float('Monto', help="Monto Total de la Factura"),
            'voucher_ids' : fields.one2many('account.payment.wizard.line', 'parent_id', 'Instrumentos de Pago'),
	    'adjust_amount': fields.float('Diferencia', help='Diferencia en Bs. existente entre la suma de montos de instrumentos de pago y el monto total de la factura'),
	    }

account_payment_wizard()

class account_payment_wizard_line(osv.osv_memory):
    _name = "account.payment.wizard.line"

    def _get_period(self, cr, uid, context=None):
        context and context or {}
        invoice_pool = self.pool.get('account.invoice')
        period = invoice_pool.browse(cr, uid, context['invoice_id'], context).period_id
        return period and period.id or False

    def onchange_journal(self, cr, uid, ids, journal_id, context=None):
        context = context and context or {}
        res = {'value':{} }
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
            account_id = journal.default_credit_account_id or journal.default_debit_account_id
            invoice = self.pool.get('account.invoice').browse(cr, uid, context['invoice_id'], context)
            wh_iva_amount = float(invoice.amount_tax*0.75)
            res['value'].update({
                        'account_id': account_id and account_id.id or '',
                        'amount': journal.type in ('iva_sale') and wh_iva_amount or 0.00,
                    })
        return res

    _columns = {
            'parent_id': fields.many2one('account.payment.wizard','Padre'),
            'journal_id': fields.many2one('account.journal', 'Tipo de Instrumento'),
	    'period_id': fields.many2one('account.period', 'Periodo'),
	    'account_id': fields.many2one('account.account', 'Cuenta'),
	    'reference': fields.char('Referencia', help="Referencia del Instrumento"),
	    'amount': fields.float('Monto'),
	    'date': fields.date('Fecha', help="Fecha del Instrumento"),
	    'partner_bank_id': fields.many2one('res.partner.bank', 'Cuenta Bancaria'),
            }

    _defaults = {
		    'period_id': _get_period,
		}

account_payment_wizard_line()
