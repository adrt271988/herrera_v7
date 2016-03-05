#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################

from osv import osv
from osv import fields


class City(osv.osv):
    '''
    Model added to manipulate separately the Cities on Partner address.
    '''
    _description='Model to manipulate Cities'
    _name ='res.city'
    _columns = {
        'state_id': fields.many2one('res.country.state','State', required=True, help="This field selects the states to which this city is associated \n"),
        'name': fields.char('City Name', size=64, required=True, help="In this field enter the name of the City \n"),
        'code': fields.char('City Code', size=3,
            help='The city code in three chars, Example: CCS for Caracas .\n', required=True),
    }
    def name_search(self, cr, user, name='', args=None, operator='ilike',
            context=None, limit=80):
        if not args:
            args = []
        if not context:
            context = {}
        ids = self.search(cr, user, [('code', '=', name)] + args, limit=limit,
                context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args,
                    limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    _order = 'code'

City()

