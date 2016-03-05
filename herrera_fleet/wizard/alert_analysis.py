# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import unicodedata
import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime, timedelta
from  dateutil.relativedelta import relativedelta


class fleet_alert_analysis(osv.osv_memory):
    """
    Analiza las alertas de servicio de vehículos y las activa según sus criterios
    """
    _name = "fleet.alert.analysis"

    logger = netsvc.Logger()

    __logger = logging.getLogger(_name)

    _columns = {
            'sure': fields.boolean("Seguro?", help="Seleccione si esta seguro de continuar"),
        }

    def alert_analysis(self,cr,uid,ids,context=None):
        if context is None:
            context = {}

        wz_brw = ids and self.browse(cr, uid, ids, context=context)[0] or False
        evalu = wz_brw and 'wz_brw.sure' or 'True'
        vehicle_obj = self.pool.get('fleet.vehicle')
        alert_obj = self.pool.get('fleet.service.alert')
        history_obj = self.pool.get('fleet.service.alert.history')
        vehicle_ids = context.get('active_ids', []) or not wz_brw and vehicle_obj.search(cr,uid,[],context=context)
        if eval(evalu):
            if vehicle_ids:
                for vehicle_id in vehicle_ids:
                    alert_ids = alert_obj.search(cr, uid , [('vehicle_id','=',vehicle_id)])
                    for alert_brw in alert_obj.browse(cr, uid, alert_ids, context):
                        cr_km = cr_horas = cr_fecha = False
                        pre_cr_km = pre_cr_horas = pre_cr_fecha = False
                        history_id = history_obj.search(cr, uid, [('alert_id', '=', alert_brw.id),('state','=','caution')])
                        for criteria in alert_brw.criteria_ids:
                            if criteria.alert_unit == 'km':
                                actual = float(vehicle_obj._get_odometer(cr, uid, [vehicle_id], 0, None, None).get(vehicle_id,0.00))
                                limite = history_id and float(alert_brw.odometer_ini + criteria.interval) or float(alert_brw.odometer_ini + criteria.pre_interval)
                                if actual >= limite:
                                    if history_id:
                                        cr_km = True
                                    else:
                                        pre_cr_km = True
                            elif criteria.alert_unit == 'horas':
                                actual = float(vehicle_obj._get_horometer(cr, uid, [vehicle_id], 0, None, None).get(vehicle_id,0.00))
                                limite = history_id and float(alert_brw.horometer_ini + criteria.interval) or float(alert_brw.horometer_ini + criteria.pre_interval)
                                if actual >= limite:
                                    if history_id:
                                        cr_horas = True
                                    else:
                                        pre_cr_horas = True
                            elif criteria.alert_unit == 'fecha':
                                fmt = '%Y-%m-%d'
                                today = datetime.strptime(datetime.now().strftime(fmt), fmt)
                                ini = datetime.strptime(criteria.date_ini, fmt)
                                d = history_id and timedelta(days=criteria.interval) or timedelta(days=criteria.pre_interval)
                                end = datetime.strptime(criteria.date_ini, fmt) + d
                                if today >= end:
                                    if history_id:
                                        cr_fecha = True
                                    else:
                                        pre_cr_fecha = True
                        if not history_obj.search(cr, uid, [('alert_id', '=', alert_brw.id),('state','=','pending')]):
                            if cr_km == True or cr_horas == True or cr_fecha == True:
                                vals = {
                                        'alert_id': alert_brw.id,
                                        'state': 'pending',
                                        'name': 'Vehiculo %s, requiere servicio de %s, correspondiente a la alerta %s' %(alert_brw.vehicle_id.name, alert_brw.service_id.name, alert_brw.name)
                                }
                                history_obj.create(cr, uid, vals, context)
                            elif pre_cr_km == True or pre_cr_horas == True or pre_cr_fecha == True:
                                vals = {
                                        'alert_id': alert_brw.id,
                                        'state': 'caution',
                                        'name': 'Aviso: Vehiculo %s, requerira servicio de %s, correspondiente a la alerta %s' %(alert_brw.vehicle_id.name, alert_brw.service_id.name, alert_brw.name)
                                }
                                history_obj.create(cr, uid, vals, context)
            else:
                raise osv.except_osv(_('Processing Error'), _('Debe seleccionar al menos un registro!'))
        else:
            raise osv.except_osv(_('Processing Error'), _('Debe seleccionar el check'))

        return {'type': 'ir.actions.act_window_close'}

fleet_alert_analysis()
