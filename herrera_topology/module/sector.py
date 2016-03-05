# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import pooler

class sector(osv.osv):

    _name = 'res.sector'
    _description = 'Sector'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(sector, self).default_get(cr, uid, fields, context=context)
        res.update({'municipality_id':context['municipality_id'],
                    'parish_id' : context['parish_id'],
                    'city_id' : context['city_id'],
                    'state_id' : context['state_id'],
                    })
        return res
        
    _columns = {
        'name': fields.char('Sector', size=128, required=True,help="In this field enter the name of the Sector"),
        'municipality_id':fields.many2one('res.municipality','Municipio',required=True, help="In this field enter the name of the municipality which is associated with the parish", domain= "[('state_id','=',state_id)]"),
        'parish_id':fields.many2one('res.parish','Parroquia',required=True,help="In this field you enter the parish to which the sector is associated",domain= "[('municipalities_id','=',municipality_id)]" ),
        'zipcode_id':fields.many2one('res.zipcode',string='Código postal',required=False,help="in this field is selected Zip Code associated with this sector"),
        'city_id':fields.many2one('res.city',string='Ciudad',required=True,help="in this field select the city associated with this State"),
        'state_id':fields.many2one('res.country.state', string='Estado', required=False, help="In this field enter the name of state associated with the country"),
    }

sector()

class inherited_res_city(osv.osv):
        _inherit = "res.city"
        
        _columns = {        
                    'code' : fields.char('Código de la Ciudad', size=4),
         }

inherited_res_city()
