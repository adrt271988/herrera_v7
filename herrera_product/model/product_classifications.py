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

import math
import re

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

#----------------------------------------------------------
# Classification Type 1
#----------------------------------------------------------
class product_classification1(osv.osv):
    
    _name  = 'product.classification1'    

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "product.classification1"
    _description = "Product Classification Type 1"
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True, select=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'parent_id': fields.many2one('product.classification1','Parent Classification', select=True, ondelete='cascade'),
        'child_id': fields.one2many('product.classification1', 'parent_id', string='Child Classifications'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of product Classifications."),
        'type': fields.selection([('view','View'), ('normal','Normal')], 'Classification Type', help="A Classification of the view type is a virtual Classification that can be used as the parent of another Classification to create a hierarchical structure."),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
    }


    _defaults = {
        'type' : lambda *a : 'normal',
    }

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from product_classification1 where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You cannot create recursive classifications.', ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]

product_classification1()

#----------------------------------------------------------
# Classification Type 2 
#----------------------------------------------------------
class product_classification2(osv.osv):
    
    _name  = 'product.classification2'
    
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "product.classification2"
    _description = "Product Classification Type 2"
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True, select=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'parent_id': fields.many2one('product.classification2','Parent Classification', select=True, ondelete='cascade'),
        'child_id': fields.one2many('product.classification2', 'parent_id', string='Child Classifications'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of product Classifications."),
        'type': fields.selection([('view','View'), ('normal','Normal')], 'Classification Type', help="A Classification of the view type is a virtual Classification that can be used as the parent of another Classification to create a hierarchical structure."),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
    }


    _defaults = {
        'type' : lambda *a : 'normal',
    }

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from product_classification2 where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You cannot create recursive classifications.', ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]

product_classification2()

#----------------------------------------------------------
# Classification Type 3
#----------------------------------------------------------
class product_classification3(osv.osv):

    _name  = 'product.classification3'
    
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "product.classification3"
    _description = "Product Classification Type 3"
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True, select=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'parent_id': fields.many2one('product.classification3','Parent Classification', select=True, ondelete='cascade'),
        'child_id': fields.one2many('product.classification3', 'parent_id', string='Child Classifications'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of product Classifications."),
        'type': fields.selection([('view','View'), ('normal','Normal')], 'Classification Type', help="A Classification of the view type is a virtual Classification that can be used as the parent of another Classification to create a hierarchical structure."),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
    }


    _defaults = {
        'type' : lambda *a : 'normal',
    }

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from product_classification3 where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You cannot create recursive classifications.', ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]

product_classification3()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
