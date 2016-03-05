# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime
from  dateutil.relativedelta import relativedelta

class fleet_desincorporate(osv.osv_memory):
    """
    Desicorpora los accesorios que no esten aptos para su uso
    """

    _name = "fleet.desincorporate"

    _columns = {
            'date_out': fields.date('Fecha de desincorporación', help="Fecha de desincorporación del accesorio", required = True),
        }

    def desincorporate(self,cr,uid,ids,context=None):
        if context is None:
            context = {}

        wz_brw = ids and self.browse(cr, uid, ids, context=context)[0] or False
        aditional_obj = self.pool.get('fleet.vehicle.aditionals')
        aditional_ids = context.get('active_ids', []) or not wz_brw and aditional_obj.search(cr,uid,[],context=context)
        if aditional_ids:
            for aditional_brw in aditional_obj.browse(cr, uid, aditional_ids, context):
                if aditional_brw.state != 'inactive':
                    aditional_obj.write(cr, uid, aditional_brw.id, {'state':'inactive', 'date_out': wz_brw.date_out})
                    if aditional_brw.vehicle_id:
                        aditional_obj.write(cr, uid, aditional_brw.id, {'vehicle_id':''})
                else:
                    raise osv.except_osv(_('Processing Error'), _('El accesorio ya se encuentra desincorporado!'))
        else:
            raise osv.except_osv(_('Processing Error'), _('Debe seleccionar al menos un registro!'))

        return {'type': 'ir.actions.act_window_close'}

fleet_desincorporate()
