# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import calendar
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import openerp.addons.decimal_precision as dp


class inherited_asset(osv.osv):

    _inherit = 'account.asset.asset'
    _description = "Activos Herrera"
    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
    #by default amount = 0  """ Esta funcion fue sobrescrita de la funcion original de los addons """

        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                if asset.prorata:
                    amount = amount_to_depr / asset.method_number
                    days = total_days - float(depreciation_date.strftime('%j'))

                    if i == 1:
                        #dayMonthEnd="%s" % (calendar.monthrange(datetime.today().year-1, datetime.today().month-1)[1])     # >> linea agregada
                        amount = (amount_to_depr / asset.method_number)  # >> Linea agregada
                        #amount = (amount_to_depr / asset.method_number) / total_days * days  << Estaba originalmente solo con esta linea en los addons
                    elif i == undone_dotation_number:
                        amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                if asset.prorata:
                    days = total_days - float(depreciation_date.strftime('%j'))
                    if i == 1:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * days
                    elif i == undone_dotation_number:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
        return amount

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + '-' + name
            res.append((record['id'], name))
        return res

    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        cr.execute("""SELECT  l.asset_id as id, SUM(abs(l.debit-l.credit)) AS amount
                      FROM account_move_line l
                      WHERE l.asset_id IN %s GROUP BY l.asset_id """, (tuple(ids),))
        res=dict(cr.fetchall())
        for asset in self.browse(cr, uid, ids, context):
            res[asset.id] = asset.purchase_value - res.get(asset.id, 0.0) - asset.salvage_value
        for id in ids:
            res.setdefault(id, 0.0)
        return res
    
    def _accumulated_depreciation(self, cr, uid, ids, name, args, context=None):
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            res[asset.id] = asset.purchase_value - asset.value_current
        for id in ids:
            res.setdefault(id, 0.0)
        return res
    
    def _periods_numbers(self, cr, uid, ids, name, args, context=None):
        res=cr.execute("""SELECT count(line.id)
                      FROM account_asset_depreciation_line as line
                      WHERE asset_id = %d and move_check is True """%ids[0])
        res=cr.dictfetchall()
        return { ids[0]:res[0].get('count',0)}
    
    def _remaining_periods(self, cr, uid, ids, name, args, context=None):
        res=cr.execute("""SELECT count(line.id)
                      FROM account_asset_depreciation_line as line
                      WHERE asset_id = %d and move_check is True """%ids[0])
        res=cr.dictfetchall()
        for asset in self.browse(cr, uid, ids, context):
            val = asset.method_number - res[0].get('count',0)
        return { ids[0]:val}


    def write(self, cr, uid, ids, vals, context=None):

        fleet_obj = self.pool.get('fleet.vehicle')

        if 'ref' in vals:
            asset = self.browse(cr, uid, ids, context=context)[0]
            if asset.check_fleet is True:
                fleet_id = fleet_obj.search(cr, uid, [('asset_id','=',ids[0])])
                fleet_obj.write(cr, uid, fleet_id, {'license_plate': vals['ref']}, context=context)
                #~ raise osv.except_osv(_('Notificación.!'),_("Sera modificada la Matrícula o código de referencia utilizado en el módulo de flota, que se encuentra vínculado a este activo."))

        return super(inherited_asset, self).write(cr, uid, ids, vals, context=context)

    def _get_code(self, cr, uid, ids):

        con = cr.execute(''' select  MAX(code) FROM account_asset_asset ''')
        con = cr.dictfetchall()
        val = con[0]['max'].replace('S','')
        value = val and val or 0
        code = str(int(value)+1).zfill(6)
        return code


    _columns = {
                 'employee_id': fields.many2one('hr.employee','Responsable', readonly=True, states={'draft':[('readonly',False)]}),
                 'inventory_id': fields.many2one('account.asset.inventory','Nro Inventario'),
                 'serial': fields.char('Serial del activo', size=25, readonly=True, states={'draft':[('readonly',False)]}),
                 'ref': fields.char('Referencia flota', size=25, readonly=True, states={'draft':[('readonly',False)]}, help="Ingrese aqui la placa, serial, referencia o numero de bastidor según la información que"),
                 'department_id': fields.many2one('hr.department','Departamento', readonly=True, states={'draft':[('readonly',False)]}),
                 'shop_id' : fields.many2one('sale.shop', 'Sucursal', readonly=True, states={'draft':[('readonly',False)]}),
                 'date_incorporation': fields.date('Fecha de incorporación', required= True, readonly=True, states={'draft':[('readonly',False)]}),
                 'date_reference': fields.date('Fecha de Compra', required= True, readonly=True, states={'draft':[('readonly',False)]}),
                 'image': fields.binary('Imagen del  Activo', help='Este campo contiene la imagen utilizada como foto del activo, limitada a 1024x1024px.', readonly=True, states={'draft':[('readonly',False)]}),
                 'date_disincorporate':fields.date('Fecha de desincorporación'),
                 'check_fleet': fields.boolean('Vincular a flota'),
                 'assigned': fields.boolean('Asignado'),
                 'value_current': fields.function(_amount_residual, method=True, digits_compute=dp.get_precision('Account'), store=True, string='Valor actual'),
                 'accumulated_depre': fields.function(_accumulated_depreciation, method=True, digits_compute=dp.get_precision('Account'), store=False, string='Depreciación acumulada'),
                 'period_number': fields.function(_periods_numbers, method=True, type='integer', store=False, string='Períodos depreciados'),
                 'remaining_period': fields.function(_remaining_periods, method=True, type='integer', store=False, string='Períodos restantes'),
                 'state': fields.selection([('draft','Borrador'),('open','En ejecución'),('close','Desincorporado')], 'Status', required=True,
                                  help="Cuando se crea un activo, el estado es 'Borrador'.\n" \
                                       "Si se confirma el activo, el estado va será 'En ejecución' y las líneas de depreciación pueden ser posteadas en la contabilidad.\n" \
                                       "Usted puede cerrar manualmente un activo cuando la depreciación finaliza. Si se contabiliza la última línea de la depreciación, el activo entra automáticamente en ese estado."),
                }

    _defaults = {

            'date_incorporation': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
            'purchase_date': datetime.today().strftime('%Y-%m-01'),
            'code': _get_code,
    }

    def onchange_departament_id(self, cr, uid, ids, employee_id):


        res = {}
        employee_obj = self.pool.get('hr.employee')
        emp_brw = employee_obj.browse(cr, uid, employee_id, context=None)
        department_id = emp_brw.department_id.id

        if department_id:

            value = {'department_id': department_id }
            res.update({'value': value})

        else:
            warning = { 'title': _('Empleado Sin Departamento Asignado !'),
                        'message': _('El empleado %s no pertenece a ningun departamento. Por favor notifique a su administrador') % (emp_brw.name)
                       }
            res.update({'warning': warning})


        return res
inherited_asset()
