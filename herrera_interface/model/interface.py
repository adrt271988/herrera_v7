# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

_DRAFT_LOG = 'En espera para ser cargado...'

class interface_pencabez(osv.osv):
    _name = "interface.pencabez"
    _description = "pencabez.txt"
    _rec_name = "pe_n2"
    _order = "pe_n2"
    
    def create_sale_order(self, cr, uid, ids, context=None):
        """ Create a Sale Order
        @return: True
        """
        if context is None:
            context = {}
        pdetalle_obj = self.pool.get('interface.pdetalle')
        sale_obj = self.pool.get('sale.order')
        vals = {}
        result = []
        for pencabez in self.browse(cr, uid, ids, context=context):
            sale_ids = sale_obj.search(cr, uid, [('origin','=',pencabez.pe_n2),('shop_id.code','=',pencabez.em0),('state','not in',['cancel'])], context=context)
            if sale_ids:
                sale = sale_obj.browse(cr, uid, sale_ids, context=context)[0]
                pencabez.write({'state':'fail','log':'Este pedido ya habia sido cargado previamente en %s'%(sale.name)})
                continue # jump to next pencabez's item
            vals = self._prepare_order(cr, uid, pencabez, context=context)
            if 'value' in vals:
                pdetalle_ids = pdetalle_obj.search(cr, uid, [('pe_n2','=',pencabez.pe_n2)], context=context)
                order_line = pdetalle_obj.create_sale_order_line(cr, uid, pdetalle_ids, vals['value'], context=context)
                if order_line:
                    vals['value'].update({'order_line':order_line})
                    res = sale_obj.create(cr, uid, vals['value'], context=context)
                    if res:
                        sale = sale_obj.browse(cr, uid, res, context=context)
                        result.append(sale.id)
                        pencabez.write({'state':'done','log':'Cargado exitosamente con numero de pedido %s'%(sale.name)})
                        for det in pdetalle_obj.browse(cr, uid, pdetalle_ids, context=context):
                            if det.state == 'draft':
                                det.write({'state':'done','log':'Cargado exitosamente en pedido de venta %s'%(sale.name)})
                    else:
                        pencabez.write({'state':'fail','log':'Ha ocurrido un problema desconocido creando el pedido!'})
                
                else:
                    pencabez.write({'state':'fail','log':'El pedido no tiene lineas!'})
            else:
                pencabez.write({'log':vals['warning'], 'state': 'fail'})
                pdetalle_ids = pdetalle_obj.search(cr, uid, [('pe_n2','=',pencabez.pe_n2)], context=context)
                for det in pdetalle_obj.browse(cr, uid, pdetalle_ids, context=context):
                    det.write({'log':vals['warning'], 'state': 'fail'})
        return result
        
    def cancel_sale_preorder(self, cr, uid, ids, context=None):
        pdetalle_obj = self.pool.get('interface.pdetalle')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context).name
        log = 'Cancelado por el usuario %s'%user
        for pencabez in self.browse(cr, uid, ids, context=context):
            pdetalle_ids = pdetalle_obj.search(cr, uid, [('pe_n2','=',pencabez.pe_n2)], context=context)
            pdetalle_obj.write(cr, uid, pdetalle_ids, {'state':'cancel', 'log': log}, context=context)
        return self.write(cr, uid, ids, {'state':'cancel', 'log': log}, context=context)
    
    def set_to_draft(self, cr, uid, ids, context=None):
        pdetalle_obj = self.pool.get('interface.pdetalle')
        for pencabez in self.browse(cr, uid, ids, context=context):
            pdetalle_ids = pdetalle_obj.search(cr, uid, [('pe_n2','=',pencabez.pe_n2)], context=context)
            pdetalle_obj.write(cr, uid, pdetalle_ids, {'state':'draft', 'log':_DRAFT_LOG}, context=context)
        return self.write(cr, uid, ids, {'state':'draft', 'log':_DRAFT_LOG}, context=context)

    def _get_payment_term(self, cr, uid, pe_condi, partner, context=None):
        cond_obj = self.pool.get('account.payment.condition')
        line_obj = self.pool.get('account.payment.term.line')
        # Valor por defecto del cliente, [prioridad = 2]
        payment_condition = partner.payment_condition and partner.payment_condition.id or False
        term_id = partner.property_payment_term and partner.property_payment_term.id or False
        if payment_condition:
            cond_brw = cond_obj.browse(cr, uid, partner.payment_condition.id, context=context)
            # Valor por defecto en la condicion de pago, [prioridad = 3]
            term_id = not term_id and cond_brw.payment_term.id or term_id
            try:
                dias = int(pe_condi)
            except:
                dias = 0
            line_id = line_obj.search(cr, uid, [('days','=',dias)], context=context)
            if line_id:
                line = line_obj.browse(cr, uid, line_id[0], context=context)
                # Tomar splo si este "term" es valido para la condicion
                if line.payment_id.id in cond_brw.term_ids:
                    # Valor por defecto en el pedido automatico, [prioridad = 1]
                    term_id = line.payment_id.id
        return term_id
    
    def _prepare_order(self, cr, uid, order, context=None):
        if context is None:
            context = {}
        vals = {}
        part_obj = self.pool.get('res.partner')
        shop_obj = self.pool.get('sale.shop')
        plan_obj = self.pool.get('sale.plan')
        line_obj = self.pool.get('sale.plan.attendance')
        shop = shop_obj.search(cr, uid, [('code','=',order.em0)], context=context)
        shop = shop and shop[0]
        pricelist = False
        salesman = False
        plan = False
        part = shop and part_obj.search(cr, uid, [('ref','=',order.pe_cli),('shop_id','=',shop)], context=context)
        if part:
            part = part_obj.browse(cr, uid, part, context=context)[0]
            addr = part_obj.address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
            pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
            payment_condition = part.payment_condition and part.payment_condition.id or False
            payment_term = self._get_payment_term(cr, uid, order.pe_condi, part, context=context)
            fiscal_position = part.property_account_position and part.property_account_position.id or False
            dedicated_salesman = part.user_id and part.user_id.id or uid
            # buscamos salesman usando shop y order.pe_ven
            plan = plan_obj.search(cr, uid, [('shop_id','=',shop),('code','=',order.pe_ven[1:])], context=context)
            plan = plan and plan_obj.browse(cr, uid, plan[0], context=context)
            #~ salesman = plan and plan.user_id and plan.user_id.id or dedicated_salesman
            salesman = plan and plan.user_id and plan.user_id.id or False
            attendance = plan and line_obj.search(cr, uid, [('plan_id','=',plan.id),('partner_id','=',part.id)], context=context)
            attendance = attendance and line_obj.browse(cr, uid, attendance[0], context=context)
            pricelist = attendance and attendance.pricelist_id and attendance.pricelist_id.id or pricelist
            date_order = '%s-%s-%s'%(order.pe_fecha[4:],order.pe_fecha[2:4],order.pe_fecha[:2])
            origin = order.pe_n2
            note = order.mensaje
            vals['value'] = {
                'partner_id': part.id,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'payment_condition': payment_condition,
                'payment_term': payment_term,
                'fiscal_position': fiscal_position,
                'user_id': salesman,
                'shop_id': shop,
                'pricelist_id': pricelist,
                'date_order': date_order, 
                'origin': origin, 
                'note': note, 
                'mode': 'auto', 
            }
        else:
            return {'warning': 'No se encontró el cliente'}
        if not plan:
            return {'warning': 'No se encontró planificacion de venta para este codigo de vendedor!'}
        if not pricelist:
            return {'warning': 'El cliente debe tener una tarifa de venta asociada, favor revisar planificacion de venta'}
        if not salesman:
            return {'warning': 'Debe definir un usuario para este codigo de vendedor, favor revisar planificacion de venta'}
        return vals

    _columns = {
        'pe_n2': fields.char('pe_n2', size=5, required=True, help="Numero de pedido"),
        'pe_n1': fields.char('pe_n1', size=1, required=True, help="sin informacion"),
        'pe_conse_na': fields.char('pe_conse_na', size=10, required=True, help="sin informacion"),
        'pe_fecha': fields.char('pe_fecha', size=8, required=True, help="Fecha cuando se tomo el pedido"),
        'pe_cli': fields.char('pe_cli', size=8, required=True, help="Codigo del cliente"),
        'pe_ven': fields.char('pe_ven', size=3, required=True, help="Numero del vendedor"),
        'pe_condi': fields.char('pe_condi', size=3, required=True, help="Condicion de pago"),
        'pe_facemi_ma': fields.char('pe_facemi_ma', size=14, required=True, help="Fecha de emision del pedido"),
        'pe_ultcon': fields.char('pe_ultcon', size=6, required=True, help="Ultima compra"),
        'pe_numfa': fields.char('pe_numfa', size=10, required=True, help="Numero de factura"),
        'pe_ng_na': fields.char('pe_ng_na', size=2, required=True, help="sin informacion"),
        'pe_fig_na': fields.char('pe_fig_na', size=8, required=True, help="sin informacion"),
        'pe_pog_na': fields.char('pe_pog_na', size=13, required=True, help="sin informacion"),
        'pe_ban_na': fields.char('pe_ban_na', size=5, help="sin informacion"),
        'pe_flete': fields.char('pe_flete', size=6, required=True, help="sin informacion"),
        'pe_dias_na': fields.char('pe_dias_na', size=3, required=True, help="sin informacion"),
        'pe_marcai_na': fields.char('pe_marcai_na', size=1, help="sin informacion"),
        'pe_marcap_na': fields.char('pe_marcap_na', size=1, help="sin informacion"),
        'pe_iva': fields.char('pe_iva', size=6, required=True, help="Monto de iva"),
        'total_monto_GV': fields.char('total_monto_GV', size=13, required=True, help="Monto gravable"),
        'desc_total': fields.char('desc_total', size=6, required=True, help="Total Descuento"),
        'mensaje': fields.char('mensaje', size=70, help="Mensaje adicional"),
        'conta': fields.char('conta', size=6, required=True, help="Correlativo"),
        'em0': fields.char('em0', size=1, help="Sucursal"),
        'state': fields.selection([
            ('draft', 'Pendiente'),
            ('fail', 'A Revisar'),
            ('cancel', 'Cancelado'),
            ('done', 'Realizado'),
            ], 'Estado',  ),
        'log': fields.text('Incidencias', help="Informe de incidencias asociadas al proceso de transferencia de la data"),
    }
    _defaults = {
        'state': 'draft',
        'log': _DRAFT_LOG,
    }
   
interface_pencabez()

class interface_pdetalle(osv.osv):
    _name = "interface.pdetalle"
    _description = "pdetalle.txt"
    _rec_name = "pe_n2"
    _order = "pe_n2, pe_conse"
    
    """ _SALE_LINE_MAP
    - model: object model
    - search: object model search field
    - line: order line field 
    - type: dataype
    - field: this model field
    """
    
    def update_sale_order(self, cr, uid, ids, context=None):
        """ update a Sale Order from line
        @return: True
        """
        #TODO: Cargar linea a pedido
        if context is None:
            context = {}
        pencabez_obj = self.pool.get('interface.pencabez')
        res = False
        #~ for pdetalle in self.browse(cr, uid, ids, context=context):
            #~ pencabez_ids = pencabez_obj.search(cr, uid, [('pe_n2','=',pdetalle.pe_n2)], context=context)
            #~ res = pencabez_obj.create_sale_order_line(cr, uid, pdetalle_ids, context=context)
        return res
    
    def create_sale_order_line(self, cr, uid, ids, order, context=None):
        lines = []
        for line in self.browse(cr, uid, ids, context=context):
            part = 'partner_id' in order and order['partner_id']
            prcl = 'pricelist_id' in order and order['pricelist_id']
            date = 'date_order' in order and order['date_order']
            vals = self._prepare_order_line(cr, uid, date, part, prcl, line, context=context)
            if 'value' in vals:
                lines.append((0,0,vals['value']))
                line.write({'log': _DRAFT_LOG, 'state': 'draft'})
            else:
                line.write({'log':vals['warning'], 'state': 'fail'})
        return lines
    
    def _prepare_order_line(self, cr, uid, date_order, partner_id, pricelist_id, line, context=None):
        if context is None:
            context = {}
        vals = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        lang = partner_obj.browse(cr, uid, partner_id).lang
        lang = lang or context.get('lang',False)
        context = {'lang': lang, 'partner_id': partner_id}
        context_partner = {'lang': lang, 'partner_id': partner_id}
        product_ids = product_obj.search(cr, uid, [('default_code','=',line.pe_produ)], context=context)
        product_id = product_ids and product_ids[0]
        if not product_id:
            return {'warning': 'No se encontró el producto'}
        product = product_obj.browse(cr, uid, product_id, context=context_partner)
        default_uom = product.uom_id and product.uom_id.id
        measure = product.measure
        qty = line.pe_uni
        name = product_obj.name_get(cr, uid, [product.id], context=context_partner)[0][1]
        if product.description_sale:
            name += '\n'+product.description_sale
        try:
            qty = float(qty)
        except:
            return {'warning': 'Cantidad del producto invalida!'}
        
        product_uos = False
        product_uos_qty = qty
        th_weight = qty * product.weight        # Round the quantity up
        vals['value'] = {   'product_uos_qty': product_uos_qty, 
                            'product_id': product_id, 
                            'product_uom': default_uom, 
                            'product_uom_qty': qty, 
                            'name': name, 
                            'delay': 7, 
                            'th_weight': th_weight,
                            'measure': measure, 
                            #~ 'type': 'make_to_stock',
                        }
        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
            product_id, qty or 1.0, partner_id, {
                    'uom': default_uom,
                    'date': date_order,
                    })[pricelist_id]
        if not price or price < 0:
            return {'warning': 'Este producto no tiene un precio valido, por favor revise la tarifa'}
        else:
            vals['value'].update({'price_unit': price})
        
        return vals
        
    _columns = {
        'pe_n2': fields.char('pe_n2', size=5, required=True, help="Numero de pedido"),
        'pe_n1': fields.char('pe_n1', size=1, required=True, help="sin informacion"),
        'pe_conse': fields.char('pe_conse', size=10, required=True, help="Secuencia de la linea"),
        'pe_produ': fields.char('pe_produ', size=12, required=True, help="Codigo del producto"),
        'pe_tipo_GV': fields.char('pe_tipo_GV', size=1, required=True, help="sin informacion"),
        'pe_dep_GV': fields.char('pe_dep_GV', size=1, required=True, help="sin informacion"),
        'pe_tran': fields.char('pe_tran', size=2, required=True, help="Tipo de transaccion"),
        'pe_uni': fields.char('pe_uni', size=10, required=True, help="Unidades (Udv)"),
        'pe_dcto': fields.char('pe_dcto', size=6, required=True, help="Descuento lineal"),
        'pe_vent': fields.char('pe_vent', size=13, required=True, help="sin informacion"),
        'pe_cost': fields.char('pe_cost', size=13, required=True, help="sin informacion"),
        'pe_vtarec': fields.char('pe_vtarec', size=13, required=True, help="sin informacion"),
        'pe_consigna': fields.char('pe_consigna', size=1, required=True, help="sin informacion"),
        'pe_fild': fields.char('pe_fild', size=2, required=True, help="sin informacion"),
        'pe_marca': fields.char('pe_marca', size=1, required=True, help="sin informacion"),
        'pe_dcto1': fields.char('pe_dcto1', size=6, required=True, help="sin informacion"),
        'conta': fields.char('conta', size=6, required=True, help="sin informacion"),
        'em0': fields.char('em0', size=1, help="Sucursal"),
        'state': fields.selection([
            ('draft', 'Pendiente'),
            ('fail', 'A Revisar'),
            ('cancel', 'Cancelado'),
            ('done', 'Realizado'),
            ], 'Estado',  ),
        'log': fields.text('Incidencias', help="Informe de incidencias asociadas al proceso de transferencia de la data"),
    }
    _defaults = {
        'state': 'draft',
        'log': _DRAFT_LOG,
    }
   
interface_pdetalle()

