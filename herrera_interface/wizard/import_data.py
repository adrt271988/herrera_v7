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

from openerp import pooler
from openerp.osv import osv, fields
from openerp import tools
from openerp.tools.translate import _
import os

class import_data(osv.osv_memory):
    _name = 'interface.import.data.wizard'
    _description = 'Importar data desde .txt'
    
    _shops = {
        'H':'BARCELONA',
        'D':'MARGARITA',
        'M':'MATURIN',
        'C':'CUMANA',
        'U':'ZULIA',
        'O':'ORDAZ',
        'G':'BOLIVAR',
        'K':'CARUPANO',
        'P':'FALCON',
    }
    _SALE_FILENAME = 'pencabez.txt'
    _SALE_LINE_FILENAME = 'pdetalle.txt'
    _SALE_MATCH_FIELD = 'pe_n2'
    _SALE_LINE_PARENT_FIELD = 'pe_n2'
    _SALE_MAP = [
            { 'sequence': 1, 'type': 'str', 'field': 'pe_n2', 'width': 5, },
            { 'sequence': 2, 'type': 'str', 'field': 'pe_n1', 'width': 1, },
            { 'sequence': 3, 'type': 'str', 'field': 'pe_conse_na', 'width': 10, },
            { 'sequence': 4, 'type': 'str', 'field': 'pe_fecha', 'width': 8, },
            { 'sequence': 5, 'type': 'str', 'field': 'pe_cli', 'width': 8, },
            { 'sequence': 6, 'type': 'str', 'field': 'pe_ven', 'width': 3, },
            { 'sequence': 7, 'type': 'str', 'field': 'pe_condi', 'width': 3, },
            { 'sequence': 8, 'type': 'str', 'field': 'pe_facemi_ma', 'width': 14, },
            { 'sequence': 9, 'type': 'str', 'field': 'pe_ultcon', 'width': 6, },
            { 'sequence': 10, 'type': 'str', 'field': 'pe_numfa', 'width': 10, },
            { 'sequence': 11, 'type': 'str', 'field': 'pe_ng_na', 'width': 2, },
            { 'sequence': 12, 'type': 'str', 'field': 'pe_fig_na', 'width': 8, },
            { 'sequence': 13, 'type': 'float', 'field': 'pe_pog_na', 'width': 13, },
            { 'sequence': 14, 'type': 'str', 'field': 'pe_ban_na', 'width': 5, },
            { 'sequence': 15, 'type': 'float', 'field': 'pe_flete', 'width': 6, },
            { 'sequence': 16, 'type': 'str', 'field': 'pe_dias_na', 'width': 3, },
            { 'sequence': 17, 'type': 'str', 'field': 'pe_marcai_na', 'width': 1, },
            { 'sequence': 18, 'type': 'str', 'field': 'pe_marcap_na', 'width': 1, },
            { 'sequence': 19, 'type': 'float', 'field': 'pe_iva', 'width': 13, },
            { 'sequence': 20, 'type': 'float', 'field': 'total_monto_GV', 'width': 13, },
            { 'sequence': 21, 'type': 'float', 'field': 'desc_total', 'width': 6, },
            { 'sequence': 22, 'type': 'str', 'field': 'mensaje', 'width': 70, },
            { 'sequence': 23, 'type': 'str', 'field': 'conta', 'width': 6, },
    ]    
    _SALE_LINE_MAP = [
            { 'sequence': 1, 'type': 'str', 'field': 'pe_n2', 'width': 5, },
            { 'sequence': 2, 'type': 'str', 'field': 'pe_n1', 'width': 1, },
            { 'sequence': 3, 'type': 'str', 'field': 'pe_conse', 'width': 10, },
            { 'sequence': 4, 'type': 'str', 'field': 'pe_produ', 'width': 12, },
            { 'sequence': 5, 'type': 'str', 'field': 'pe_tipo_GV', 'width': 1, },
            { 'sequence': 6, 'type': 'str', 'field': 'pe_dep_GV', 'width': 1, },
            { 'sequence': 7, 'type': 'str', 'field': 'pe_tran', 'width': 2, },
            { 'sequence': 8, 'type': 'float', 'field': 'pe_uni', 'width': 10, },
            { 'sequence': 9, 'type': 'float', 'field': 'pe_dcto', 'width': 6, },
            { 'sequence': 10, 'type': 'float', 'field': 'pe_vent', 'width': 13, },
            { 'sequence': 11, 'type': 'float', 'field': 'pe_cost', 'width': 13, },
            { 'sequence': 12, 'type': 'float', 'field': 'pe_vtarec', 'width': 13, },
            { 'sequence': 13, 'type': 'str', 'field': 'pe_consigna', 'width': 1, },
            { 'sequence': 14, 'type': 'str', 'field': 'pe_fild', 'width': 2, },
            { 'sequence': 15, 'type': 'str', 'field': 'pe_marca', 'width': 1, },
            { 'sequence': 16, 'type': 'float', 'field': 'pe_dcto1', 'width': 6, },
            { 'sequence': 17, 'type': 'str', 'field': 'conta', 'width': 6, },
    ]    

    _columns = {
        'data': fields.selection([
            ('all', 'Todos'),
            ('sales', 'Pedidos de venta'),
            ], 'Archivo',  ),
        'create_sale_order': fields.boolean('Crear pedidos',help='Proceder a la creacion de pedidos en el sistema'),
        'sure': fields.boolean('Estas seguro?',help='Validar si desea proceder con la operación'),
    }
    def _cast_madi_data(self, value, new_type):
        result = value.strip()
        try:
            if new_type == 'date':
                result = '%s-%s-%s'%(value[4:],value[2:4],value[:2])
            elif new_type == 'float':
                result = value[-1:] in ['+','-'] and eval('%s(%s%s)'%(new_type,value[-1:],value[:-1])) or eval('%s(%s)'%(new_type,value)) or '0.0'
            elif new_type == 'int':
                result = int(value)
            #~ elif new_type == 'boolean':
                #~ result = int(value)==1 or False
        except:
            result = new_type == 'int' and '0' or \
                    new_type == 'float' and '0.0'
        return str(result)
        
    def _import_sale(self, cr, uid, ids, path, shop, context=None):
        archive = open('%s/%s/%s'%(path,self._shops[shop],self._SALE_FILENAME))
        archive_line = open('%s/%s/%s'%(path,self._shops[shop],self._SALE_LINE_FILENAME))
        result = []
        sales = []
        lines = []
        pencabez_obj = self.pool.get('interface.pencabez')
        pdetalle_obj = self.pool.get('interface.pdetalle')
        fields = dict(map(lambda x: (x['sequence'], x['field']), self._SALE_MAP))
        widths = dict(map(lambda x: (x['field'], x['width']), self._SALE_MAP))
        dtypes = dict(map(lambda x: (x['field'], x['type']), self._SALE_MAP))
        fields_line = dict(map(lambda x: (x['sequence'], x['field']), self._SALE_LINE_MAP))
        widths_line = dict(map(lambda x: (x['field'], x['width']), self._SALE_LINE_MAP))
        dtypes_line = dict(map(lambda x: (x['field'], x['type']), self._SALE_LINE_MAP))
        # LINEAS
        for line in archive_line:
            sale_order_line = {'em0':shop}
            begin_line = 0
            for seq_line in sorted(fields_line):
                field_line = fields_line[seq_line]
                #~ if field_line == self._
                width_line = widths_line[field_line]
                dtype_line = dtypes_line[field_line]
                end_line = begin_line + width_line # hasta
                value_line = self._cast_madi_data(line[begin_line:end_line],dtype_line)
                #~ value_line = line[begin_line:end_line].strip()
                sale_order_line.update({field_line:value_line})
                # actualizamos el indice
                begin_line = end_line
            #~ print sale_order_line
            lines.append(sale_order_line)
        # ENCABEZADO
        for head in archive:
            sale_order = {'em0':shop}
            sale_order_lines = []
            begin = 0
            for seq in sorted(fields):
                field = fields[seq]
                width = widths[field]
                dtype = dtypes[field]
                end = begin + width # hasta
                value = self._cast_madi_data(head[begin:end],dtype)
                #~ value = head[begin:end].strip()
                sale_order.update({field:value})
                # actualizamos el indice
                begin = end
            # asociacion de lineas relacionadas
            for line in lines:
                if line[self._SALE_LINE_PARENT_FIELD] == sale_order[self._SALE_MATCH_FIELD]:
                    sale_order_lines.append(line)
            if sale_order_lines:
                sale_order.update({'sale_order_lines':sale_order_lines})
            sales.append(sale_order)
        # procedemos a guardar en los modelos de herrera_interface
        for sale in sales:
            lines = sale.pop('sale_order_lines')
            pencabez_ids = pencabez_obj.search(cr, uid, [(self._SALE_MATCH_FIELD,'=',sale[self._SALE_MATCH_FIELD]),('em0','=',shop)], context=context)
            if not pencabez_ids and sale[self._SALE_MATCH_FIELD]:
                pencabez_id = pencabez_obj.create(cr, uid, sale, context=context)
                pencabez_id and result.append(pencabez_id)
                for line in lines:
                    pdetalle_obj.create(cr, uid, line, context=context)
        return result
    
    def import_data(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        pencabez_obj = self.pool.get('interface.pencabez')
        sale_obj = self.pool.get('sale.order')
        wzr = ids and self.browse(cr, uid, ids, context=context)[0]
        path = self.pool.get('ir.config_parameter').get_param(cr, uid, 'herrera_interface.import_path')
        if not path:
            raise osv.except_osv(_('Directorio no encontrado!'),
                         _('No hay directorio configurado para esta accion, para mas informacion contacte a su administrador') )
        data = wzr.data
        pencabez_ids = []
        sale_ids = []
        for shop in self._shops:
            shop_path = '%s/%s'%(path,self._shops[shop])
            txt_files = [f for f in os.listdir(shop_path) if f.endswith('.txt')]
            for txt in txt_files:
                if txt == self._SALE_FILENAME and data in ['sales','all']:
                    # Importar pedidos
                    pencabez_ids.extend(self._import_sale(cr, uid, ids, path, shop, context=context))
        # Crear y validar pedidos
        if pencabez_ids and wzr.create_sale_order:
            sale_ids.extend(pencabez_obj.create_sale_order(cr, uid, pencabez_ids, context=context))
            print 'sale_ids',sale_ids
            for sale_id in sale_ids:
                print 'sale_id',sale_id
                sale_obj.action_button_approved(cr, uid, [sale_id], context=context)
        return {'type': 'ir.actions.act_window_close'}
        
    _defaults = {
         'sure': lambda *a: False,
    }
    
import_data()
