import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime
from time import gmtime, strftime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class account_asset_report(osv.osv_memory):

    _name = 'account.asset.report'
    _columns = {
                'report_type': fields.selection([('L','Listado de activos'),
                                                 ('I','Activos incorporados'),
                                                 ('D','Activos desincorporados'),
                                                 ('T','Nota de translado'),
                                                 ('A','Nota de asignacion')
                                                 ], 'Selecione reporte', required=True,
                                                   help="Muestra los tipos de reportes disponibles para ser generados."),
                'report_group':fields.selection([('C','Categoria'),
                                                 ('S','Sucursal'),
                                                 ('P','Activo padre'),
                                                 ], 'Agrupar reporte por:',
                                                   help="Muestra los grupos en los que se pueden clasificar los activos para generar los listados."),
                'select_categ':fields.selection([('1','Seleccionar Categoria'),
                                                 ('0','Todas las Categorias'),
                                                     ], 'Seleccione:'),
                'select_shop': fields.selection([('1','Seleccionar Sucursal'),
                                                 ('0','Todas las Sucursales'),
                                                     ], 'Seleccione:'),
                'select_parent':fields.selection([('1','Seleccionar Activo Padre'),
                                                 ('0','Todos los Activos Padre'),
                                                     ], 'Seleccione:'),
                'shop_id' :fields.many2one('sale.shop','Oficina'),
                'asset_id' :fields.many2one('account.asset.asset','Activo Padre', domain=[('parent_id','=',False)] ),
                'date_from':fields.date('Fecha desde'),
                'date_until':fields.date('Fecha hasta'),
                'period_id': fields.many2one('account.period', 'Periodo:'),
                'employee_id': fields.many2one('hr.employee','Responsable'),
                'category_id': fields.many2one('account.asset.category','Categoria'),
                'department_id': fields.many2one('hr.department','Departamento'),
                'asset_ids': fields.many2many('account.asset.asset', 'asset_shop_ids_rel', 'asset_id', 'shop_id', 'Activos',domain="[('state','!=','close')]"),
                }

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False


    _defaults = {
            'date_from': time.strftime('%Y-%m-01'),
            'date_until': time.strftime('%Y-%m-%d'),
            'period_id': _get_period,
    }

    def action_report(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        date_current = strftime("%A, %d %B de %Y", gmtime())
        datas={'ids':context.get('active_ids',[])}#la variable (data) almacena los ids activos
        res=self.read(cr,uid,ids, context=context)#la variable (res) almacena las lecturas realizadas
        res=res and res[0] or {}
        datas['form']=res
        report = res['report_type']=='L' and 'asset.list' or \
                 res['report_type']=='T' and 'asset.transfer' or \
                 res['report_type']=='D' and 'asset.desincorporated' or \
                 res['report_type']=='I' and 'asset.incorporated' or \
                 res['report_type']=='A' and 'asset.assignment'

        res['date_current']=date_current
        period = self.pool.get('account.period').browse(cr,uid, res['period_id'][0], context=context)
        res.update({'date_start': period.date_start , 'date_stop': period.date_stop})

        return{
                'type':'ir.actions.report.xml',   #Tipo de accion que se va a ejecutar
                'report_name': report,   #Nombre que se se definio en el .xml de report
                'datas':res,  #Se muestra los datos en la variable
              }

account_asset_report()
