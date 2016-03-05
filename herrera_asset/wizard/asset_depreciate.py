# -*- coding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
import webbrowser

class account_asset_depreciate_process(osv.osv_memory):

    _name = 'account.asset.depreciate.process'
    _columns = {
                'period_id' :fields.many2one('account.period','Periodo', required=True),
                }

    def action_depreciate(self, cr, uid, ids, context=None):
        can_close = False
        if context is None:
            context = {}
        values = self.read(cr,uid,ids, context=context)

        period_id = values[0]['period_id'][0]
        period_date = values[0]['period_id'][1] #ejm: '03/2014'
        period = period_date.split('/')

        depreciate_obj = self.pool.get('account.asset.depreciation.line')
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        dep_lines_ids = []
        
        depreciate_ids = cr.execute(''' SELECT asdl.id as id_dep_line
                                        FROM account_asset_depreciation_line as asdl
                                        JOIN account_asset_asset aaa on aaa.id = asdl.asset_id
                                        WHERE EXTRACT('month' from depreciation_date) = '%s' and EXTRACT('year' from depreciation_date) = '%s'
                                        and move_check is FALSE and aaa.state = 'open' '''% (period[0], period[1]))
        depreciate_ids = cr.dictfetchall()
        if not depreciate_ids:
            raise osv.except_osv(_('Notificacion..!'),_('No se encontraron activos para depreciar en el periodo seleccionado, por favor ingrese un nuevo periodo o verifique que sus activos esten confirmados y posean una Tabla de Amortizacion.'))
        for i in depreciate_ids:
            dep_lines_ids.append(i['id_dep_line'])

        for line in depreciate_obj.browse(cr, uid, dep_lines_ids, context=context):
            date_stop = period_obj.browse(cr, uid,period_id, context=context)['date_stop'] #fecha del ultimo dia del periodo seleccionado para depreciar
            depreciation_date = time.strftime('%Y-%m-%d') < date_stop and time.strftime('%Y-%m-%d') or date_stop
            #depreciation_date = context.get('depreciation_date') or time.strftime('%Y-%m-%d')
            ctx = dict(context, account_period_prefer_normal=True)
            #period_ids = period_obj.find(cr, uid, depreciation_date, context=ctx) #busca el periodo fiscal
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = (line.asset_id.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = line.asset_id.name
            reference = line.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_id and period_id or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_id and period_id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_id and period_id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                'analytic_account_id': line.asset_id.category_id.account_analytic_id.id,
                'date': depreciation_date,
                'asset_id': line.asset_id.id
            })
            depreciate_obj.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)

        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            asset.write({'value_current': asset.value_residual })

            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual): #ultimo asiento de depreciacion
                asset.write({'state': 'open' })
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'confirm.xml',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'confirm',
                #'res_id': created_move_ids,
                'target': 'new',
                'context': context,
                }
        #return created_move_ids

    def action_txt(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        values = self.read(cr,uid,ids, context=context)
        period_id = values[0]['period_id'][0]
        periodo = values[0]['period_id'][1].replace('/','-')
        move_line_obj = self.pool.get('account.move.line')
        #archivo = open('/mnt/gsist06/OpenERP/txt/salida/'+periodo+'.txt','w')
        ruta = '/home/openerp/txt-activos/'+periodo+'.txt'
        archivo = open(ruta,'w')

        query = cr.execute(''' SELECT ac.code, ac.name as cuenta, line.name, line.credit as credito, line.debit as debito
                                FROM account_move_line as line
                                JOIN account_account ac on ac.id = line.account_id
                                JOIN account_journal jo on jo.id = line.journal_id
                                WHERE line.period_id = %s and jo.code = 'DADA' ORDER BY line.name'''%period_id)
        query = cr.dictfetchall()

        for line in query:
            cuenta = str(line['code']).zfill(11)
            descrip =  len(line['name']) > 25 and  line['name'][0:25] or line['name'].ljust(25,'-')

            if line['debito'] > 0.00:
                tipo = '1'
                monto = str(int(line['debito']*100)).zfill(10)
                archivo.write("%s\n"%(cuenta+tipo+descrip+monto))
            else:
                tipo = '2'
                monto= str(int(line['credito']*100)).zfill(10)
                archivo.write("%s\n"%(cuenta+tipo+descrip+monto))

        archivo.close()
        
        
        return {
                'type': 'ir.actions.act_window',
                'name': 'confirm.xml',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'confirm',
                'target': 'new',
                'context': context,
                }

account_asset_depreciate_process()

   #------------Abrir un URL---------------
   #webbrowser.open(ruta, new=0, autoraise=True)
    #~  import webbrowser
        # def open_url(self, cr, uid, ids, context):
        #~ drawing_url = self.browse(cr, uid, ids)[0].urls
        #~ if drawing_url:
            #~ return { 'type': 'ir.actions.act_url', 'url': drawing_url, 'nodestroy': True, 'target': 'new' }
        #~ return True
