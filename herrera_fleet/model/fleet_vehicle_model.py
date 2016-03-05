# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class inherited_fleet_vehicle_model(osv.Model):
    _inherit = "fleet.vehicle.model"

    def _check_model_name(self, cr, uid, ids, context=None):
        model_ids = self.search(cr, uid , [], context=context)
        lst = [x.modelname.lower() for x in self.browse(cr, uid, model_ids, context=context) if x.modelname and x.id not in ids]
        for model_brw in self.browse(cr, uid, ids, context=context):
            if model_brw.modelname and model_brw.modelname.lower() in lst:
                return False
        return True

    _constraints = [
                        (_check_model_name, "Nombre de modelo duplicado", ["modelname"]),
                    ]

inherited_fleet_vehicle_model()

class inherited_fleet_vehicle_model_brand(osv.Model):
    _inherit = "fleet.vehicle.model.brand"

    def _check_brand_name(self, cr, uid, ids, context=None):
        brand_ids = self.search(cr, uid , [], context=context)
        lst = [x.name.lower() for x in self.browse(cr, uid, brand_ids, context=context) if x.name and x.id not in ids]
        for brand_brw in self.browse(cr, uid, ids, context=context):
            if brand_brw.name and brand_brw.name.lower() in lst:
                return False
        return True

    _constraints = [
                        (_check_brand_name, "Nombre de marca duplicado", ["name"]),
                    ]

inherited_fleet_vehicle_model_brand()
