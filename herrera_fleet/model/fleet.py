# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from datetime import datetime
from openerp import pooler, tools

class inherited_fleet_vehicle_cost(osv.Model):
    _inherit = "fleet.vehicle.cost"

    def clean_line(self, cr, uid, ids, cost_subtype_id, context = None):
        res = {}
        value = {}
        value['amount'] = value['subtotal'] = value['tax'] = 0.00
        res['value'] = value
        return res
    
    def onchange_subtotal(self, cr, uid, ids, cost_subtype_id, amount, context = None):
        res = {}
        vendor_id = context.get('vendor_id')
        if not vendor_id:
            raise osv.except_osv(_('Processing Error'), _('Debe seleccionar un Proveedor!'))
        else:
            iva_bool = self.pool.get('res.partner').browse(cr, uid, vendor_id, context).vat_subjected
            type_brw = self.pool.get('fleet.service.type').browse(cr, uid, cost_subtype_id, context)
	    tax_bs = 0.00
            if iva_bool is True:
                if type_brw.iva is True:
		    taxes = type_brw.product_id.supplier_taxes_id
		    if taxes:
			for tax in taxes:
			    tax = float(tax.amount * amount)
			    tax_bs += tax
			value = {'tax': tax_bs, 'subtotal': amount + tax_bs}
                else:
                    value = {'subtotal': amount}
                res.update({'value': value})
        return res
    
    _columns = {
        'horometer_id': fields.many2one('fleet.vehicle.horometer', 'Horometer'),
        'tax': fields.float('Monto Impuesto (IVA)'),
        'subtotal': fields.float('Subtotal'),
    }

inherited_fleet_vehicle_cost()


class inherited_fleet_vehicle_odometer(osv.Model):
    _inherit = "fleet.vehicle.odometer"

    _columns = {
        'responsible_id': fields.many2one('hr.employee', 'Chofer', domain = [('job_id.name','=','DESPACHADOR')]),
        'driver_id': fields.many2one('fleet.drivers', 'Chofer'),
    }

inherited_fleet_vehicle_odometer()

class inherited_fleet_service_type(osv.Model):
    _inherit = "fleet.service.type"

    def create(self, cr, uid, vals, context={}):
	account_obj = self.pool.get('account.account')
	uom = self.pool.get('product.uom').search(cr, uid, [('measure','=','hora')])
	#### Cableando por defecto el impuesto de servicios a los servicios
	acc_tax_id = account_obj.search(cr, uid, [('code','=','18101003')])
	tax_id = self.pool.get('account.tax').search(cr, uid, [('account_collected_id','=',acc_tax_id[0])])
        if vals['category'] == 'service':
            product = {
                        'name': vals['name'].upper(),
                        'default_code': vals['name'][0:3].upper(),
                        'type': 'service',
                        'measure': 'unidad',
                        'measure_po': 'unidad',
                        'uom_id': uom and uom[0] or '',
                        'uom_po_id': uom and uom[0] or '',
                        'property_account_income': account_obj.search(cr, uid, [('code','=','40001001')])[0],
                        'property_account_expense': account_obj.search(cr, uid, [('code','=','11501001')])[0],
                        'categ_id': self.pool.get('product.category').search(cr, uid, [('name','=','SERVICIOS Y CONSUMIBLES DE FLOTA')])[0],
			'supplier_taxes_id': tax_id and [(6, 0, tax_id)] or [],
            }
            product_id = self.pool.get('product.product').create(cr, uid, product, context)
            vals['product_id'] = product_id
        return super(inherited_fleet_service_type, self).create(cr, uid, vals, context)
    
    _columns = {
        'product_id': fields.many2one('product.product','Servicio Asociado', help = 'Producto tipo servicio asociado'),
        'iva': fields.boolean('Aplica IVA', help = 'Si este campo esta activo, se calculara el IVA para este servicio'),
        'account_id' : fields.many2one("account.account", "Cuenta Contable"),
    }

inherited_fleet_service_type()


class inherited_fleet_vehicle_log_services(osv.Model):
    _name = 'fleet.vehicle.log.services'
    _inherit = ["fleet.vehicle.log.services", "mail.thread"]
    _order = 'id desc'

    def set_done(self, cr, uid, ids, context=None):
        service_brw = self.browse(cr, uid, ids[0], context)
        account_obj = self.pool.get('account.invoice')
        if service_brw.inv_ref:
            self.write(cr, uid, ids, {'state': 'done'})
            one2many = []
            invoice_line_vals = {}
            for line_service in service_brw.cost_ids:
		tax_ids = []
                product_id = line_service.cost_subtype_id.product_id
                account_id = line_service.cost_subtype_id.account_id
                subtype_name = line_service.cost_subtype_id.name
		taxes = product_id.supplier_taxes_id
		if taxes:
		    for t in taxes:
			tax_ids.append(t.id)
                if not product_id:
                    raise osv.except_osv(_('Processing Error'), _('El servicio %s no tiene producto asociado!'%subtype_name))
                if not account_id and service_brw.outcome_to_vehicle is False:
                    raise osv.except_osv(_('Processing Error'), _('El servicio %s no tiene cuenta contable asignada!'%subtype_name))
                invoice_line_vals = {
                    'product_id': product_id.id,
                    'name': product_id.name,
                    'account_id': service_brw.outcome_to_vehicle and service_brw.vehicle_id.account_id.id or account_id.id,
                    'quantity': 1,
                    'price_unit': line_service.amount,
                    'invoice_line_tax_id': line_service.cost_subtype_id.iva and [(6, 0, tax_ids)] or [],
                }
                one2many.append((0,0,invoice_line_vals))
                
            vendor_id = service_brw.vendor_id
            account_payable = service_brw.vendor_id.property_account_payable
            if not vendor_id:
                    raise osv.except_osv(_('Processing Error'), _('Seleccione un proveedor!'))
            if not account_payable:
                    raise osv.except_osv(_('Processing Error'), _('El proveedor no posee cuenta contable asociada!'))
            invoice_vals = {
                        'partner_id': vendor_id.id,
                        'type': 'in_invoice',
                        'origin': service_brw.name,
                        'supplier_invoice_number': service_brw.inv_ref,
                        'account_id': account_payable.id,
                        'invoice_line': one2many,
                        'journal_id': self.pool.get('account.journal').search(cr, uid, [('code','=','DC'),('type','=','purchase')])[0],
            }
            account_obj.create(cr, uid, invoice_vals, context = context)
            self.message_post(cr, uid, ids , body=_('La %s ha sido Cerrada!... Puede revisar la factura generada en el modulo de Contabilidad') % (service_brw.name), context=context)
        else:
            raise osv.except_osv(_('Processing Error'), _('Debe ingresar el numero de factura de proveedor!'))
        return True

    def set_confirm(self, cr, uid, ids, context=None):
        name = self.browse(cr, uid, ids[0], context).name
        self.write(cr, uid, ids, {'state': 'confirmed'})
        self.message_post(cr, uid, ids , body=_('La %s se encuentra Confirmada!') % (name), context=context)
        return True

    def set_cancel(self, cr, uid, ids, context=None):
        name = self.browse(cr, uid, ids[0], context).name
        self.write(cr, uid, ids, {'state': 'cancel'})
        self.message_post(cr, uid, ids , body=_('La %s ha sido anulada!') % (name), context=context)
        return True

    def onchange_vehicle(self, cr, uid, ids, vehicle_id):
        res = {}
        vehicle_obj = self.pool.get('fleet.vehicle')
        vehicle_brw = vehicle_obj.browse(cr, uid, vehicle_id)
        value = {
                    'odometer': self._values_for_onchange(cr, uid, ids, vehicle_id, 'fleet.vehicle.odometer', None, None).get(vehicle_id),
                    'horometer': self._values_for_onchange(cr, uid, ids, vehicle_id, 'fleet.vehicle.horometer', None, None).get(vehicle_id),
                    'responsible_id': vehicle_brw.responsible_id and vehicle_brw.responsible_id.id or '',
                }
        res.update({'value': value})
        return res

    def _values_for_onchange(self, cr, uid, ids, vehicle_id, model, arg, context):
        res = dict.fromkeys(ids, 0)
        model_obj = self.pool.get(model)
        ids = model_obj.search(cr, uid, [('vehicle_id', '=', vehicle_id)], limit=1, order='value desc')
        if len(ids) > 0:
            res[vehicle_id] = model_obj.browse(cr, uid, ids[0], context=context).value
        else:
            res[vehicle_id] = 0.00
        return res

    def _get_odometer(self, cr, uid, ids, name, arg, context):
        res = dict.fromkeys(ids, 0)
        cost_id = self.browse(cr, uid, ids[0], context).cost_id.id
        cost_brw = self.pool.get('fleet.vehicle.cost').browse(cr, uid, cost_id)
        res[ids[0]] = cost_brw and cost_brw.odometer_id.value or 0.00
        return res

    def _set_odometer(self, cr, uid, id, name, value, args=None, context=None):
        if not value:
            return False
        service_brw = self.browse(cr, uid, id, context)
        data = {'value': value, 'date': service_brw.date, 'vehicle_id': service_brw.vehicle_id.id, 'responsible_id': service_brw.responsible_id.id}
        odometer_id = self.pool.get('fleet.vehicle.odometer').create(cr, uid, data, context=context)
        cost_id = service_brw.cost_id.id
        return self.pool.get('fleet.vehicle.cost').write(cr, uid, cost_id, {'odometer_id': odometer_id}, context=context)

    def _get_horometer(self, cr, uid, ids, name, arg, context):
        res = dict.fromkeys(ids, 0)
        if ids:
            cost_id = self.browse(cr, uid, ids[0], context).cost_id.id
            cost_brw = self.pool.get('fleet.vehicle.cost').browse(cr, uid, cost_id)
            res[ids[0]] = cost_brw and cost_brw.horometer_id.value or 0.00
        return res

    def _set_horometer(self, cr, uid, id, name, value, args=None, context=None):
        if not value:
            return False
        service_brw = self.browse(cr, uid, id, context)
        data = {'value': value, 'date': service_brw.date, 'vehicle_id': service_brw.vehicle_id.id, 'responsible_id': service_brw.responsible_id.id}
        horometer_id = self.pool.get('fleet.vehicle.horometer').create(cr, uid, data, context=context)
        cost_id = service_brw.cost_id.id
        return self.pool.get('fleet.vehicle.cost').write(cr, uid, cost_id, {'horometer_id': horometer_id}, context=context)

    _columns = {
        'name': fields.char('Codigo', size=64, select=True),
        'state': fields.selection([
            ('draft', 'O/S Borrador'),
            ('confirmed', 'O/S Confirmada'),
            ('done', 'O/S Cerrada'),
            ('cancel', 'O/S Anulada'),
            ], 'Status O/S', readonly=True, select=True, track_visibility='onchange', help="""
            * O/S Borrador: orden de servicio sin confirmar\n
            * O/S Confirmada: orden de servicio confirmada, en espera para su facturacion\n
            * O/S Cerrada: orden de servicio cerrada, ya esta facturada y se crea cuenta por pagar asociada\n
            * O/S Cerrada: orden de servicio anulada"""
        ),
        'odometer': fields.function(_get_odometer, fnct_inv=_set_odometer, type='float', string='Valor odometro', help='Valor del odometro al momento del servicio', states={'confirmed': [('readonly', True)],'cancel': [('readonly', True)],'done': [('readonly', True)]}),
        'horometer': fields.function(_get_horometer, fnct_inv=_set_horometer, type='float', string='Valor horometro', help='Valor del horometro al momento del servicio (horas)'),
        'responsible_id': fields.many2one('hr.employee', 'Chofer', domain = [('job_id.name','=','DESPACHADOR')]),
        'driver_id': fields.many2one("fleet.drivers", "Chofer"),
        'total_amount': fields.float('Monto Total'),
        'total_tax': fields.float('Monto Impuesto de O/S'),
        'create_uid': fields.many2one('res.users', 'User', readonly=1),
        'shop': fields.related('vehicle_id', 'shop_id', type = 'many2one', relation = 'sale.shop', string = 'Sucursal'),
        'outcome_to_vehicle': fields.boolean('Gastos a Cuenta del Vehiculo', help="Si esta seleccionado, los gastos se cargaran automaticamente a las cuenta contable del vehiculo"),
    }

    _defaults = {
                    'state': 'draft',
                    'outcome_to_vehicle': True,
                }

    def create(self, cr, uid, vals, context={}):
        last_odometer = self._values_for_onchange(cr, uid, [], vals['vehicle_id'], 'fleet.vehicle.odometer', None, None).get(vals['vehicle_id']),
        last_horometer = self._values_for_onchange(cr, uid, [], vals['vehicle_id'], 'fleet.vehicle.horometer', None, None).get(vals['vehicle_id']),
        current_odometer = float(vals['odometer'])
        current_horometer = float(vals['horometer'])
        if current_odometer == 0.00 and current_horometer == 0.00:
            raise osv.except_osv(_('Processing Error'), _('Debe ingresar un valor de odometro u horometro, ambos permanecen en 0.00!'))
            return False
        else:
            if current_odometer > last_odometer[0] or current_horometer > last_horometer[0]:
                if (not 'name' in vals) or (vals['name'] == False):
                    vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'fleet.vehicle.log.services')
                total_amount = 0.00
                total_tax = 0.00
                for i in vals['cost_ids']:
                    for j in i:
                        if type(j) == dict:
                            total_tax += j.get('tax')
                            total_amount += j.get('subtotal')
                vals['total_tax'] = total_tax
                vals['total_amount'] = total_amount
                service_id = super(inherited_fleet_vehicle_log_services, self).create(cr, uid, vals, context)
                self.message_post(cr, uid, [service_id], body=_('La %s ha sido creada!') % (vals['name']), context=context)
                return service_id
            else:
                raise osv.except_osv(_('Processing Error'), _('Los valores de odometro u horometro no pueden estar por debajo!'))
                return False

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        keys = vals.keys()
        cr.execute('''  SELECT total_amount, total_tax FROM fleet_vehicle_log_services WHERE id = %s ''' %ids[0])
        res = cr.dictfetchall()
        if 'cost_ids' in keys:
            total_amount = 0.00
            total_tax = 0.00
            for i in vals['cost_ids']:
                for j in i:
                    if type(j) == dict:
                        total_tax += j.get('tax')
                        total_amount += j.get('subtotal')
            old_tax = res[0]['total_tax'] and res[0]['total_tax'] or 0.00
            old_total = res[0]['total_amount'] and res[0]['total_amount'] or 0.00
            vals.update({'total_tax': old_tax + total_tax, 'total_amount': old_total + total_amount})
        super(inherited_fleet_vehicle_log_services, self).write(cr, uid, ids, vals, context=context)
        return True

inherited_fleet_vehicle_log_services()


class inherited_fleet_vehicle(osv.Model):

    _inherit = "fleet.vehicle"

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
    
    def _order_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0), ids))
        try:
            for vehicle in self.browse(cr, uid, ids, context=context):
                service_ids = self.pool.get('fleet.vehicle.log.services').search(cr, uid, [('vehicle_id','=',vehicle.id),('state','not in',['done','cancel'])])
                res[vehicle.id] = len(service_ids)
        except:
            pass
        return res

    def _alert_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0), ids))
        try:
            for vehicle in self.browse(cr, uid, ids, context=context):
                alert_ids = self.pool.get('fleet.service.alert.history').search(cr, uid, [('vehicle','=',vehicle.id),('state','=','pending')])
                res[vehicle.id] = len(alert_ids)
        except:
            pass
        return res

    def _get_odometer(self, cr, uid, ids, odometer_id, arg, context):
        res = dict.fromkeys(ids, 0)
        for record in self.browse(cr,uid,ids,context=context):
            ids = self.pool.get('fleet.vehicle.odometer').search(cr, uid, [('vehicle_id', '=', record.id)], limit=1, order='value desc')
            if len(ids) > 0:
                res[record.id] = self.pool.get('fleet.vehicle.odometer').browse(cr, uid, ids[0], context=context).value
        return res

    def _set_odometer(self, cr, uid, id, name, value, args=None, context=None):
        if value:
            date = fields.date.context_today(self, cr, uid, context=context)
            vehicle_brw = self.browse(cr, uid, id, context)
            data = {'value': value, 'date': date, 'vehicle_id': id, 'responsible_id': vehicle_brw.responsible_id.id}
            self.pool.get('fleet.vehicle.odometer').create(cr, uid, data, context=context)

    def _get_horometer(self, cr, uid, ids, horometer_id, arg, context):
        res = dict.fromkeys(ids, 0)
        for record in self.browse(cr,uid,ids,context=context):
            ids = self.pool.get('fleet.vehicle.horometer').search(cr, uid, [('vehicle_id', '=', record.id)], limit=1, order='value desc')
            if len(ids) > 0:
                res[record.id] = self.pool.get('fleet.vehicle.horometer').browse(cr, uid, ids[0], context=context).value
        return res

    def _set_horometer(self, cr, uid, id, name, value, args=None, context=None):
        if value:
            date = fields.date.context_today(self, cr, uid, context=context)
            vehicle_brw = self.browse(cr, uid, id, context)
            data = {'value': value, 'date': date, 'vehicle_id': id, 'responsible_id': vehicle_brw.responsible_id.id}
            return self.pool.get('fleet.vehicle.horometer').create(cr, uid, data, context=context)

    def onchange_search_asset(self, cr, uid, ids, license_plate, contracted):
        res = {}
        if not contracted:
            asset_obj = self.pool.get('account.asset.asset')
            asset_id = asset_obj.search(cr, uid, [('ref','=',license_plate.upper()),('check_fleet','=',True),('assigned','=',False),('state','=','open')])
            if asset_id:
                asset_brw = asset_obj.browse(cr, uid, asset_id[0], context=None)
                value = {
                            'asset_id': asset_id[0],
                            'shop_id': asset_brw.shop_id and asset_brw.shop_id.id or '',
                            'acquisition_date': asset_brw.purchase_date and asset_brw.purchase_date or '',
                            'car_value': asset_brw.purchase_value and asset_brw.purchase_value or '',
                            'responsible_id': asset_brw.employee_id and asset_brw.employee_id.id or '',
                        }
                res.update({'value': value})
            else:
                warning = { 'title': _('Vehiculo no encontrado!'),
                            'message': _('La placa %s no esta asociada a ningun activo fijo o ya el vehiculo ha sido registrado como parte de la flota de Herrera!') % (license_plate)
                           }
                res.update({'warning': warning})
        else:
            vehicle_id = self.pool.get('fleet.vehicle').search(cr, uid, [('license_plate','=',license_plate.upper())])
            if vehicle_id:
                warning = { 'title': _('Placa duplicada!'),
                            'message': _('La placa %s ya ha sido registrada como parte de la flota de Herrera!') % (license_plate)
                           }
                res.update({'warning': warning})
        return res

    def create(self, cr, uid, vals, context={}):
        if vals['contracted'] is True and vals['partner_id'] == 1:
            raise osv.except_osv(_('Processing Error'), _('El vehiculo es contratado, por lo tanto no pertenece a Herrera C.A.!'))
            return False
        else:
            vals['license_plate'] = vals['license_plate'].upper()
            state_id = self.pool.get('fleet.vehicle.state').search(cr, uid, [('name','=','Operativo')])[0]
            asset_obj = self.pool.get('account.asset.asset')
            asset_id = asset_obj.search(cr, uid, [('ref','=',vals['license_plate']),('check_fleet','=',True),('assigned','=',False),('state','=','open')])
            vals.update({'asset_id': asset_id and asset_id[0] or '', 'state_id':state_id})
            asset_id and self.pool.get('account.asset.asset').write(cr, uid, vals['asset_id'], {'assigned': True}, context=context)
            return super(inherited_fleet_vehicle, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.asset_id.check_fleet is True:
                self.pool.get('account.asset.asset').write(cr, uid, [move.asset_id.id], {'check_fleet': False, 'ref': ''})
        return super(inherited_fleet_vehicle, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Activo Fijo', help = 'Codigo de Activo Fijo en Herrera C.A.'),
        'responsible_id' : fields.many2one("hr.employee", "Chofer"),
        'driver' : fields.many2one("fleet.drivers", "Chofer"),
        'shop_id' : fields.many2one("sale.shop", "Sucursal"),
        'account_id' : fields.many2one("account.account", "Cuenta Contable"),
        'aditional_ids' : fields.one2many('fleet.vehicle.aditionals', 'vehicle_id', 'Accesorios'),
        'motor_number' : fields.char("Serial Motor", size = 20, help = 'Serial del Motor'),
        'odometer': fields.function(_get_odometer, fnct_inv=_set_odometer, type='float', string='Ultimo orometro', help='Odometer measure of the vehicle at the moment of this log'),
        'last_horometer': fields.function(_get_horometer, fnct_inv=_set_horometer, type='float', string='Ultimo horometro', help='Ultimo valor del horometro al momento del ingreso del vehiculo en el sistema (horas)'),
        'min_volumetric_capacity' : fields.float("Minima Capacidad Volumetrica", help = 'Minima capacidad volumetrica del vehiculo a ser despachada (metros cubicos)'),
        'volumetric_capacity' : fields.float("Maxima Capacidad Volumetrica", help = 'Maxima capacidad volumetrica del vehiculo a ser despachada (metros cubicos)'),
        'min_capacity_kgs' : fields.float("Minima Capacidad en Kgs.", help = 'Minima capacidad en kilogramos del vehiculo a ser despachada'),
        'capacity_kgs' : fields.float("Maxima Capacidad en Kgs.", help = 'Maxima capacidad en kilogramos del vehiculo a ser despachada'),
        'gps' : fields.boolean("GPS", help = 'Posee dispositivo GPS?'),
        'active_vehicle' : fields.boolean("Activo"),
        'order_count': fields.function(_order_count, string='O/S Pendientes', type='integer'),
        'alert_count': fields.function(_alert_count, string='Alertas Pendientes', type='integer'),
        'contracted' : fields.boolean("Vehiculo Contratado?", help = 'Permite diferenciar si el vehiculo es propio de la empresa o es contratado a terceros'),
        'partner_id' : fields.many2one("res.partner", "Propietario", help="Compañia propietaria del vehiculo"),
        'age': fields.integer('Ano de Fabricacion', size = 4, help = 'Año de fabricacion del vehiculo'),
        'image': fields.binary("Logo", help="Limitada hasta 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Imagen de tamaño medio", type="binary", multi="_get_image",
            store={
                'fleet.vehicle': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of this contact. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Imagen de tamaño pequeño", type="binary", multi="_get_image",
            store={
                'fleet.vehicle': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
    }

    _defaults = {'active_vehicle': True, 'partner_id': 1, 'contracted': False}

    _sql_constraints = [
        ('license_plate_uniq', 'unique (license_plate)', 'Ya existe esta placa!'),
        ('motor_number_uniq', 'unique (motor_number)', 'Serial del motor duplicado!'),
        ('vin_sn_uniq', 'unique (vin_sn)', 'Numero de Bastidor/Chasis duplicado!'),
    ]

inherited_fleet_vehicle()

class fleet_vehicle_horometer(osv.Model):
    _name='fleet.vehicle.horometer'
    _description='Horometer log for a vehicle'
    _order='date desc'

    def _vehicle_log_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            name = record.vehicle_id.name
            if record.date:
                name = name+ ' / '+ str(record.date)
            res[record.id] = name
        return res

    _columns = {
        'name': fields.function(_vehicle_log_name_get_fnc, type="char", string='Name', store=True),
        'date': fields.date('Fecha'),
        'value': fields.float('Valor Horometro', group_operator="max"),
        'vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle', required=True),
        'responsible_id': fields.many2one('hr.employee', 'Chofer', domain = [('job_id.name','=','DESPACHADOR')]),
        'driver_id': fields.many2one('fleet.drivers', 'Chofer'),
    }
    _defaults = {
        'date': fields.date.context_today,
    }

fleet_vehicle_horometer()

class inherit_fleet_vehicle_state(osv.Model):
    _inherit='fleet.vehicle.state'

    _columns = {
        'set_inactive': fields.boolean('Inactiva Vehiculo?', help="Define si el estatus provoca que el vehiculo este inactivo"),
    }

inherit_fleet_vehicle_state()

class fleet_vehicle_state_log(osv.Model):
    _name='fleet.vehicle.state.log'
    _description='Vehicle states change log'
    _order='date desc'

    def onchange_vehicle(self, cr, uid, ids, vehicle_id):
        res = {}
        vehicle_obj = self.pool.get('fleet.vehicle')
        vehicle_brw = vehicle_obj.browse(cr, uid, vehicle_id)
        value = {
                    'state_id': vehicle_brw.state_id and vehicle_brw.state_id.id or '',
                }
        res.update({'value': value})
        return res

    def create(self, cr, uid, vals, context={}):
        state_id = int(vals['state_id'])
        set_inactive = self.pool.get('fleet.vehicle.state').browse(cr,uid,state_id,context).set_inactive
        if set_inactive == True:
            var = False
        else:
            var = True
        self.pool.get('fleet.vehicle').write(cr, uid, [int(vals['vehicle_id'])], {'state_id': state_id, 'active_vehicle': var})
        return super(fleet_vehicle_state_log, self).create(cr, uid, vals, context)

    _columns = {
        'date': fields.date('Fecha'),
        'vehicle_id': fields.many2one('fleet.vehicle', 'Vehiculo', required=True),
        'state_id': fields.many2one('fleet.vehicle.state', 'Estado', required=True),
    }
    _defaults = {
        'date': fields.date.context_today,
    }

fleet_vehicle_state_log()
