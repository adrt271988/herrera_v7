# -*- encoding: utf-8 -*-
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools


class freight_route(osv.osv):
    
    _name='freight.route'
    _description='Rutas de flete de la Empresa.'

    def _get_detail_lines(self, cr, uid, context=None):
        res = []
        if context is None:
            context = {}
        vals = ['CC','PF','CF']
        for i in vals:
                res.append((0,0,{
                        'type': i,
                        }))
        return res

    _columns = {
    
        'name': fields.char('Ruta', required=True),
        'code': fields.char('Código', size=5),
        'rank':fields.char('Rango de distancia', size=64, required=True),
        'shop_id': fields.many2one('sale.shop', 'Sucursal'),
        'detail_ids': fields.one2many('details.freight.route','freight_route_id','Detalles'),
    }
    #~ _defaults = {
        #~ 'detail_ids': _get_detail_lines,
    #~ }

freight_route()

class details_freight_route(osv.osv):
    
    _name='details.freight.route'
    _description='Detalles de las Rutas de flete de la Empresa.'

    _columns = {
    
        'weight' : fields.float('Bs.X Peso (Kg)'),
        'volume' : fields.float('Bs.X Volumen (m3)'),
        'boxes' : fields.float('Bs.X Cajas (UdV)'),
        'type': fields.selection([('CC', 'Chofer Contratado'), ('PF', 'Porcentaje Fijo'), ('CF', 'Chofer Fijo')], 'Tipo', required=True),
        'freight_route_id':fields.many2one('freight.route', 'Detalles'),
    }

details_freight_route()


