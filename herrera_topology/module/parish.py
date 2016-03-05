#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################

from osv import osv
from osv import fields
from tools.translate import _

class parish(osv.osv):

    _name ='res.parish'
    _description='Model to manipulate Parish'
    
    _columns = {
        'name':fields.char(size=128, required=True, readonly=False, string="Parish", help="In this field enter the name of the Parish \n"),
        'municipalities_id':fields.many2one('res.municipality','Municipality',required=True, help="In this field enter the name of the municipality which is associated with the parish\n"),
        'sector_ids':fields.one2many('res.sector','parish_id','Sector',required=True, help="In this field enter the name of sectors associated with the parish"),
    }
    _defaults = {
        'name': lambda *a: None,
    }
parish()
