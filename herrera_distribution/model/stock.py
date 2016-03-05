# -*- encoding: utf-8 -*-
from openerp import netsvc
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from datetime import datetime
import time
from openerp.tools import float_compare

class inherit_stock_move_distribution(osv.osv):
    _inherit = "stock.move"
    
    _columns = {
        'distro_line_id': fields.many2one('stock.distribution.line', 'Item de Despacho'),
        'distribution_confirm': fields.boolean('Confirmación del Operador de Movimiento listo para ser Despachado')
    }

inherit_stock_move_distribution()

class inherit_stock_picking(osv.osv):
    _inherit = 'stock.picking'

    #~ def _check_chained_location_customer(self, cr, uid, ids, field_name, arg, context=None):
        #~ """ Check if picking only contain moves to output location.
        #~ @return: Dictionary of values
        #~ """
        #~ res = {}
        #~ if not ids:
            #~ return res
        #~ cr.execute("""select mov.picking_id, 
                #~ count(mov.id),
                #~ count(
                    #~ case 
                    #~ when loc.chained_location_type = 'customer' 
                    #~ then
                    #~ 1
                    #~ end
                #~ )
            #~ from
                #~ stock_move as mov
            #~ join
                #~ stock_location as loc
            #~ on
                #~ mov.location_dest_id = loc.id
            #~ where
                #~ mov.picking_id IN %s
            #~ group by
                #~ mov.picking_id""",(tuple(ids),))
        #~ for pick, total, output in cr.fetchall():
            #~ res[pick] = (total == output)
        #~ return res
        
    def _get_picking_value(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds values for picking list function fields.
        @return: Dictionary of values
        """
        res = {}
        for id in ids:
            res[id] = {
                'product_qty': 0.0, 
                'weight': 0.0, 
                'volume': 0.0, 
                'ind_payment_units': 0.0, 
            }
        if not ids:
            return res
        cr.execute("""select sm.picking_id as picking_id, 
                sum(sm.product_qty) as product_qty, 
                sum(tm.weight*sm.product_qty) as weight, 
                sum(tm.volume*sm.product_qty) as volume, 
                sum(tm.standard_price) as cost, 
                sum(
                    case 
                        when pr.ind_payment = True 
                    then
                        sm.product_qty 
                    else 
                        0 
                    end
                ) as ind_payment
            from
                stock_move as sm
            join
                stock_picking as sp 
            on
                sm.picking_id = sp.id
            join
                product_product as pr
            on
                sm.product_id = pr.id
            join
                product_template as tm
            on
                pr.product_tmpl_id = tm.id
            where
                sm.picking_id IN %s
            group by
                sm.picking_id""",(tuple(ids),))
        for pick, qty, weight, volume, cost, ind in cr.fetchall():
            res[pick]['product_qty'] = qty
            res[pick]['weight'] = weight
            res[pick]['volume'] = volume
            res[pick]['cost'] = cost
            res[pick]['ind_payment_units'] = ind
        return res
    
    def _date_to_string(self, cr, uid, ids, name, args, context=None):
        """ Forms complete name of location from parent location to child location.
        @return: Dictionary of values
        """
        res = {}
        for p in self.browse(cr, uid, ids, context=context):
            res[p.id] = p.date[:10]
        return res

    _columns = {
        'state_id': fields.related('partner_id', 'state_id', type='many2one', relation='res.country.state', string='Estado', store=True),
        'municipality_id': fields.related('partner_id', 'municipality_id', type='many2one', relation='res.municipality', string='Municipio', store=True),
        'sector_id': fields.related('partner_id', 'sector', type='many2one', relation='res.sector', string='Sector', store=True),
        'freight_route_id': fields.related('partner_id', 'freight_route_id', type='many2one', relation='freight.route', string='Ruta', store=True, help = 'Ruta del flete'),
        'cost': fields.function(_get_picking_value, type='float', string="Costo (Bs)", multi="picking_list", help = 'Valoracion en bolivares, se usa el ultimo costo como base'),
        'product_qty': fields.function(_get_picking_value, type='float', string="Cantidad UdV", multi="picking_list", help = 'Cantidad de Unidades de Venta'),
        'weight': fields.function(_get_picking_value, type='float', string="Peso (Kgs)", multi="picking_list", help = 'Peso en Kilogramos'),
        'volume': fields.function(_get_picking_value, type='float', string="Volumen", multi="picking_list", help = 'Volumen en m3'),
        'ind_payment_units': fields.function(_get_picking_value, type='float', string="Cantidad de Unidades de Pago Independiente", multi="picking_list", help = 'Cantidad de Unidades de Pago Independiente'),
        'day': fields.function(_date_to_string, type='char', size=10, string="Fecha", store=True),
        'distribution_id': fields.many2one('stock.distribution', 'Despacho', help=u'Número de Despacho en donde fue enviado este albarán'),
        
    }
    
inherit_stock_picking()

class inherited_stock_picking_out(osv.osv):
    """
    Herrera customizations for stock.picking.out model
    """
    _inherit = "stock.picking.out"

    def action_view_distro(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = {}
        distro_ids = []
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
	picking_brw = self.browse(cr, uid, ids, context=context)
	distro_ids = map(lambda x : x.distribution_id.id, picking_brw)
	distro_ids = list(set(distro_ids))
        result = mod_obj.get_object_reference(cr, uid, 'herrera_distribution', 'stock_distribution_act')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #choose the view_mode accordingly
        if len(distro_ids) == 1:
            res = mod_obj.get_object_reference(cr, uid, 'herrera_distribution', 'stock_distribution_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = distro_ids and distro_ids[0] or False
        elif len(distro_ids) > 1:
            result['domain'] = "[('id','in',["+','.join(map(str, distro_ids))+"])]"
        else:
            result = mod_obj.get_object_reference(cr, uid, 'herrera_distribution', 'create_distribution_action1')
            id = result and result[1] or False
            result = act_obj.read(cr, uid, [id], context=context)[0]
        return result

# Redefinition of the new field in order to update the model stock.picking.out in the orm
# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed

    _columns = {
        'distribution_id': fields.many2one('stock.distribution', 'Despacho', help=u'Número de Despacho en donde fue enviado este albarán'),
    }

inherited_stock_picking_out()
