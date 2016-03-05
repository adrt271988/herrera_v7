# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class asset_inventory_line(osv.osv):

    _name = "asset.inventory.line"
    _description = "Lineas del inventario de activos"
    _rec_name = 'asset_id'
    _columns = {
        'asset_id' : fields.many2one('account.asset.asset', string="Descripción", required=True, ondelete='CASCADE',domain=[('state','!=','close')]),
        'serial': fields.char('Serial',size=25),
        'shop_id' :  fields.many2one('sale.shop', 'Sucursal' , required=True),
        'department_id': fields.many2one('hr.department','Departamento', required=True,),
        'employee_id': fields.many2one('hr.employee', 'Responsable', required=True),
        'wizard_id' : fields.many2one('account.asset.inventory', string="Wizard", ondelete='CASCADE'),
        'code': fields.char('Codigo de busqueda'),
    
    }

    def onchange_asset_inv(self, cr, uid, ids, code_search):
        
        res = {}
        asset_obj = self.pool.get('account.asset.asset')
        asset_id = asset_obj.search(cr, uid, ['|',('code','=',code_search),('serial','=',code_search)])
        if asset_id:
            asset = asset_obj.browse(cr, uid, asset_id)
            
            shop_id= asset[0].shop_id.id
            value = { 'asset_id': asset_id[0],
                      'serial': asset[0].serial, 
                      'shop_id': shop_id, 
                      'department_id':asset[0].department_id.id, 
                      'employee_id': asset[0].employee_id.id 
                    }
            res.update({'value': value })

        else:
            warning = { 'title': _('Activo no Encontrado !'),
                        'message': _('El codigo %s no hace referencia a ningun activo existente. Por favor verifique que el codigo ingresado este correcto') % (code_search)
                       }
            res.update({'warning': warning})

        return res
