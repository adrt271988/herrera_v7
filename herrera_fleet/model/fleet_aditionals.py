# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class fleet_vehicle_aditionals(osv.osv):
    """
    Herrera new model for aditionals of vehicles
    """
    _name = "fleet.vehicle.aditionals"

    def _get_odometer(self, cr, uid, ids, odometer_id, arg, context):
        res = dict.fromkeys(ids, 0)
        vehicle_id = self.browse(cr,uid,ids[0],context).vehicle_id.id
        search_ids = self.pool.get('fleet.vehicle.odometer').search(cr, uid, [('vehicle_id', '=', vehicle_id)], limit=1, order='value desc')
        if len(search_ids) > 0:
            res[ids[0]] = self.pool.get('fleet.vehicle.odometer').browse(cr, uid, search_ids[0], context=context).value
        return res

    def _get_horometer(self, cr, uid, ids, odometer_id, arg, context):
        res = dict.fromkeys(ids, 0)
        vehicle_id = self.browse(cr,uid,ids[0],context).vehicle_id.id
        search_ids = self.pool.get('fleet.vehicle.horometer').search(cr, uid, [('vehicle_id', '=', vehicle_id)], limit=1, order='value desc')
        if len(search_ids) > 0:
            res[ids[0]] = self.pool.get('fleet.vehicle.horometer').browse(cr, uid, search_ids[0], context=context).value
        return res

    def check_serial(self, cr, uid, ids, context=None):
        add_brw = self.browse(cr, uid, ids[0], context)
        lista = self.search(cr,uid,[('serial','=',add_brw.serial),('type_id','=',add_brw.type_id.id),('state','=','active')])
        lista.remove(ids[0])
        if lista:
            raise osv.except_osv(_('Processing Error'), _('Serial duplicado!'))
        return True

    def check_limit(self, cr, uid, ids, context=None):
        vehicle_id = self.pool.get('fleet.vehicle.aditionals').browse(cr, uid, ids[0], context).vehicle_id.id
        if vehicle_id:
            cr.execute('SELECT type_id, COUNT(add.type_id) as contador FROM fleet_vehicle_aditionals add WHERE add.vehicle_id = %d GROUP BY add.type_id' %int(vehicle_id))
            for rec in cr.dictfetchall():
                limit = self.pool.get('fleet.vehicle.aditionals.type').browse(cr, uid, rec.get('type_id'), context).limit
                if limit:
                    if rec.get('contador') > limit:
                        raise osv.except_osv(_('Processing Error'), _('Excede el número de accesorios por tipo!'))
        return True

    _columns = {
        'name' : fields.char('Codigo', size = 8, help = "Codigo interno del Accesorio", required = True),
        'serial' : fields.char("Serial",size = 20, help = "Serial del Accesorio", required = True),
        'type_id': fields.many2one('fleet.vehicle.aditionals.type', "Categoria", required = True),
        'brand_id': fields.many2one('fleet.vehicle.aditionals.brand', "Marca"),
        'use_id': fields.many2one('fleet.vehicle.aditionals.use', "Tipo"),
        'vehicle_id':fields.many2one('fleet.vehicle', 'Vehiculo', help="Vehículo al cual el accesorio pertenece" ),
        'size':fields.many2one('fleet.vehicle.aditionals.size','Tamano', help = 'Tamaño del Rin/ Batería / Gato / etc.'),
        'state':fields.selection([
            ('active', 'Activo'),
            ('inactive', 'Desincorporado'),
            ], 'Status', select=True, help="""
            * Activo: Accesorio en buen estado\n
            * Desincorporado: Accesorio inactivo o dañado"""),
        'date_in': fields.date('Fecha de Ingreso', required=True),
        'date_out': fields.date('Fecha de Desincorporacion'),
        'odometer': fields.function(_get_odometer, type='float', string='Odometro', help='Odómetro del vehículo al momento de cargar el accesorio'),
        'horometer': fields.function(_get_horometer, type='float', string='Horometro', help='Horómetro del vehículo al momento de cargar el accesorio'),
    }

    _defaults = {
                    'state': 'active',
                    'date_in': fields.date.context_today,
                    }

    _constraints = [
                        (check_limit, "Excede el número límite de accesorios para este tipo", ["type_id"]),
                        (check_serial, "Serial duplicado", ["serial"]),
                    ]

fleet_vehicle_aditionals()

class fleet_vehicle_aditionals_type(osv.osv):
    _name = "fleet.vehicle.aditionals.type"

    _columns = {
        'name' : fields.char('Categoria', size = 50, help = "Categoría del Accesorio", required = True),
        'limit' : fields.float('Límite', help = "Número de accesorios permitidos de este tipo en el vehículo"),
    }

fleet_vehicle_aditionals_type()

class fleet_vehicle_aditionals_use(osv.osv):
    _name = "fleet.vehicle.aditionals.use"

    _columns = {
        'name' : fields.char('Tipo', size = 50, help = "Tipo del Accesorio", required = True),
    }

fleet_vehicle_aditionals_type()

class fleet_vehicle_aditionals_brand(osv.osv):
    _name = "fleet.vehicle.aditionals.brand"

    _columns = {
        'name' : fields.char('Marca', size = 50, help = "Marca del Accesorio", required = True),
    }

fleet_vehicle_aditionals_brand()

class fleet_vehicle_aditionals_size(osv.osv):
    _name = "fleet.vehicle.aditionals.size"

    _columns = {
        'name' : fields.char('Tamaño', size = 50, help = "Tamaño del Accesorio", required = True),
    }

fleet_vehicle_aditionals_size()
