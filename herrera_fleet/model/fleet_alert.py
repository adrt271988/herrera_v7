# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import datetime

class fleet_service_alert(osv.Model):
    _name='fleet.service.alert'
    _description='Configurar Alertas de Servicios'

    def _get_odometer(self, cr, uid, ids, name, arg, context):
        res = dict.fromkeys(ids, 0)
        alert_brw = self.browse(cr, uid, ids[0], context = context)
        for record in self.pool.get('fleet.vehicle').browse(cr,uid,[alert_brw.vehicle_id.id],context=context):
            odometer_ids = self.pool.get('fleet.vehicle.odometer').search(cr, uid, [('vehicle_id', '=', record.id)], limit=1, order='value desc')
            if len(odometer_ids) > 0:
                res[ids[0]] = self.pool.get('fleet.vehicle.odometer').browse(cr, uid, odometer_ids[0], context=context).value
        return res

    def _get_horometer(self, cr, uid, ids, horometer_id, arg, context):
        res = dict.fromkeys(ids, 0)
        alert_brw = self.browse(cr, uid, ids[0], context = context)
        for record in self.pool.get('fleet.vehicle').browse(cr,uid,[alert_brw.vehicle_id.id],context=context):
            horometer_ids = self.pool.get('fleet.vehicle.horometer').search(cr, uid, [('vehicle_id', '=', record.id)], limit=1, order='value desc')
            if len(horometer_ids) > 0:
                res[ids[0]] = self.pool.get('fleet.vehicle.horometer').browse(cr, uid, horometer_ids[0], context=context).value
        return res

    _columns = {
        'name': fields.char('Código', help = 'Código de la alerta'),
        'vehicle_id': fields.many2one('fleet.vehicle', 'Vehículo', required=True),
        'service_id': fields.many2one('fleet.service.type', 'Tipo de Servicio', required = True),
        'criteria_ids' : fields.one2many('fleet.service.alert.criteria', 'alert_id', 'Criterios'),
        'odometer_ini': fields.function(_get_odometer, type='float', string='Odometro Inicial', store = True),
        'horometer_ini': fields.function(_get_horometer, type='float', string='Horometro Inicial', store = True),
    }

fleet_service_alert()

class fleet_service_alert_criteria(osv.Model):
    _name='fleet.service.alert.criteria'
    _description='Criterios de Alertas'

    def _check_criteria(self,cr,uid,ids,context=None):
        criteria_brw = self.browse(cr,uid,ids[0],context=context)
        if criteria_brw.alert_unit == 'fecha':
            if criteria_brw.date_ini == '':
                raise osv.except_osv(_('Warning!'), _('Ingrese una fecha de inicio, para el intervalo de tiempo!!'))
        else:
            if criteria_brw.interval <= 0.00 or criteria_brw.pre_interval < 0.00:
                raise osv.except_osv(_('Warning!'), _('El intervalo debe ser mayor a cero!!'))
        return True

    _columns = {
        'alert_id': fields.many2one('fleet.service.alert', 'Tipo de Servicio', invisible = True),
        'alert_unit': fields.selection([
            ('km', 'Kilómetros'),
            ('horas', 'Horas'),
            ('fecha', 'Fechas'),
            ], 'Tipo de Alerta', select=True, help="Criterio para evaluar las alertas de servicios"
        ),
        'interval': fields.float('Intervalo', help = 'Valor del Intervalo (km, horas, dias)'),
        'pre_interval': fields.float('Intervalo Preventivo', help = 'Valor del Intervalo de Alerta Preventiva (km, horas, dias)'),
        'date_ini': fields.date('Fecha de Inicio'),
    }

    _constraints = [
                        (_check_criteria, 'El intervalo debe ser mayor a cero',['interval', 'pre_interval', 'date_ini', 'date_end']),
                    ]

fleet_service_alert_criteria()

class fleet_service_alert_history(osv.Model):
    _name='fleet.service.alert.history'
    _description='Historico de Alertas'

    def confirm_service(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        history_brw = self.browse(cr, uid, ids[0], context)
        alert_id = history_brw.alert_id.id
        alert_obj = self.pool.get('fleet.service.alert')
        alert_brw = alert_obj.browse(cr, uid, alert_id, context)
        vehicle_id = alert_brw.vehicle_id.id
        vehicle_obj = self.pool.get('fleet.vehicle')
        for criteria in alert_brw.criteria_ids:
            if criteria.alert_unit == 'km':
                o_actual = vehicle_obj._get_odometer(cr, uid, [vehicle_id], 0, None, None).get(vehicle_id,0.00)
                nuevo_limite_o = float(o_actual) + float(criteria.interval)
                print 'LIMITE ODO:',nuevo_limite_o
                alert_obj.write(cr, uid, [alert_id], {'odometer_ini': nuevo_limite_o})
            elif criteria.alert_unit == 'horas':
                h_actual = vehicle_obj._get_horometer(cr, uid, [vehicle_id], 0, None, None).get(vehicle_id,0.00)
                nuevo_limite_h = float(h_actual) + float(criteria.interval)
                print 'LIMITE HOR:',nuevo_limite_h
                alert_obj.write(cr, uid, [alert_id], {'horometer_ini': nuevo_limite_h})
            elif criteria.alert_unit == 'fecha':
                criteria_one2many = []
                vals = {'date_ini': datetime.datetime.now()}
                criteria_one2many.append((1,criteria.id,vals))
                alert_obj.write(cr, uid, [alert_id], {'criteria_ids': criteria_one2many})
        history_ids = self.search(cr, uid, [('alert_id','=',alert_id)])
        self.write(cr, uid, history_ids, {'date': datetime.datetime.now(), 'state': 'confirmed'})
        return True

    _columns = {
        'alert_id': fields.many2one('fleet.service.alert', 'Alerta', invisible = True),
        'reference': fields.many2one('fleet.vehicle.log.services', 'Referencia O/S'),
        'state': fields.selection([
            ('pending', 'Pendiente'),
            ('caution', 'Aviso'),
            ('confirmed', 'Realizado'),
            ], 'Estado', select=False, help="Estado del servicio"
        ),
        'date': fields.date('Fecha', help = 'Fecha de confirmación del servicio'),
        'name': fields.char('Descripción', help = 'Descripción de la alerta de servicio'),
        'alert': fields.related('alert_id', 'name', type = 'char', string = 'Código Alerta'),
        'vehicle': fields.related('alert_id', 'vehicle_id', type = 'many2one', relation = 'fleet.vehicle', string = 'Vehiculo'),
        'service': fields.related('alert_id', 'service_id', type = 'many2one', relation = 'fleet.service.type', string = 'Servicio'),
    }

fleet_service_alert_history()
