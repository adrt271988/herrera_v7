# -*- encoding: utf-8 -*-
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools


class fleet_drivers(osv.osv):
    
    _name='fleet.drivers'
    _description='Choferes Fijos y Contratados de la Compañia.'
    _inherits = {'resource.resource': "resource_id"}

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result
    
    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
        

    _columns = {
    
        #necesitamos un campo relacionado con el fin de ser capaz de ordenar el empleado por su nombre
        'name_related': fields.related('resource_id', 'name', type='char', string='Nombre', readonly=True, store=True),
        'driver_type': fields.selection([('F', 'Fijo'),('C', 'Contratado')], 'Condición', required=True),
        'country_id': fields.many2one('res.country', 'Nacionalidad'),
        'birthday': fields.date('Fecha de Nacimiento'),
        'entry_date': fields.date('Fecha de ingreso'),
        'cedula': fields.char('N° de Cédula', size=12, required=True),
        'rif': fields.char('RIF', size=14),
        'state_id' : fields.many2one('res.country.state', 'Estado'),
        'shop_id': fields.many2one('sale.shop', 'Sucursal'),
        'municipality_id' : fields.many2one('res.municipality', 'Municipio'),
        'parish_id' : fields.many2one('res.parish', 'Parroquia'),
        'address': fields.char('Urb/Calle/AV/Sector', size=240),
        'search': fields.char('Buscar', size=14, ),
        'gender': fields.selection([('male', 'Masculino'),('female', 'Femenino')], 'Sexo'),
        'marital': fields.selection([('single', 'Soltero'), ('married', 'Casado'), ('widower', 'Viudo'), ('divorced', 'Divorciado')], 'Estado Civil'),
        'department_id':fields.many2one('hr.department', 'Departamento'),
        'address_id': fields.many2one('res.partner', 'Dirección de Empleo'),
        'bank_account':fields.char('Numero de Cuenta Bancaria', size=24),
        #~ 'bank_account_id':fields.many2one('res.partner.bank', 'Numero de Cuenta Bancaria', help="Employee bank salary account"),
        'work_phone': fields.char('Telefono Trabajo', size=32, readonly=False),
        'mobile_phone': fields.char('Telefono Mobil', size=32, readonly=False),
        'work_email': fields.char('Email', size=240),
        'work_location': fields.char('Dirección de Oficina', size=32),
        'notes': fields.text('Notas'),
        'parent_id': fields.many2one('hr.employee', 'Jefe Inmediato'),
        'category_ids': fields.many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', 'Categoria'),
        'resource_id': fields.many2one('resource.resource', 'Resource', ondelete='cascade', required=True),
        'job_id': fields.many2one('hr.job', 'Cargo'),
        'code': fields.char('Código', size=5),
        'account_payable':fields.many2one('account.account', 'Cuenta a pagar'),
        'account_receivable':fields.many2one('account.account', 'Cuenta a cobrar'),
        'withholding_iva':fields.many2one('taxes.withholding', 'Retención IVA'),
        'withholding_islr':fields.many2one('taxes.withholding', 'Retención ISLR'),
        #~ 'color': fields.integer('Color Index'),
        #~ 'city': fields.related('address_id', 'city', type='char', string='Ciudad'),
        'login': fields.related('user_id', 'login', type='char', string='Login', readonly=1),
        'last_login': fields.related('user_id', 'date', type='datetime', string='Ultima Conexion', readonly=1),
        'image': fields.binary("Photo", help="Este campo contiene la imagen utilizada como foto para el empleado, limitado a 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image, string="Medium-sized photo", type="binary", multi="_get_image",
            store = {'fleet.drivers': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10), },
            help="""Foto de tamaño mediano del empleado. Es automáticamente. Cambia de tamaño como una imagen 128x128px, con relación de aspecto conservado.
                    Utilice este campo en las vistas de formulario o algunos puntos de vista kanban."""),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Smal-sized photo", type="binary", multi="_get_image",
            store = {'fleet.drivers': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),},
            help="""Foto de pequeño tamaño del empleado. Es automáticamente. Cambia de tamaño como una imagen 64x64px con relación de aspecto conservado.
                    Utilice este campo donde se requiera una imagen pequeña."""),
        

    }

    _order='name_related'
    
    def onchange_address_id(self, cr, uid, ids, address, context=None):
        if address:
            address = self.pool.get('res.partner').browse(cr, uid, address, context=context)
            return {'value': {'work_phone': address.phone, 'mobile_phone': address.mobile}}
        return {'value': {}}

    def onchange_company(self, cr, uid, ids, company, context=None):
        address_id = False
        if company:
            company_id = self.pool.get('res.company').browse(cr, uid, company, context=context)
            address = self.pool.get('res.partner').address_get(cr, uid, [company_id.partner_id.id], ['default'])
            address_id = address and address['default'] or False
        return {'value': {'address_id' : address_id}}

    def onchange_search_driver(self, cr, uid, ids, val, context=None):
        res = {}
        if val:
            employee_obj = self.pool.get('hr.employee')
            employee_id = employee_obj.search(cr, uid, [('identification_id','ilike',val)])
            
            if employee_id:
                employee_brw = employee_obj.browse(cr, uid, employee_id, context=context)

                value = {'cedula': employee_brw[0].identification_id, 
                         'marital':employee_brw[0].marital,
                         'image_medium':employee_brw[0].image_medium,
                         'name': employee_brw[0].name,
                         'job_id': employee_brw[0].job_id.id,
                         'bank_account_id':employee_brw[0].bank_account_id.id,
                         'work_phone':employee_brw[0].work_phone,
                         'country_id':employee_brw[0].country_id.id,
                         'parent_id':employee_brw[0].parent_id.id,
                         'department_id':employee_brw[0].department_id.id,
                         'mobile_phone':employee_brw[0].mobile_phone,
                         'birthday':employee_brw[0].birthday,
                         'work_email':employee_brw[0].work_email,
                         'work_location': employee_brw[0].work_location,
                         'gender':employee_brw[0].gender,
                         'passport_id':employee_brw[0].passport_id,
                         'entry_date':employee_brw[0].entry_date,
                         }
                res.update({'value': value})
            else:
                warning = { 'title': _('Chofer no Encontrado !'),
                            'message': _('El N° de Cedula o Rif %s no hace referencia a ningun chofer existente. Por favor verifique que el Chofer que desea ingresar sea de condicion fijo o que la informacion ingresada este correcta.') % (val)
                           }
                res.update({'warning': warning})

        return res
fleet_drivers()


