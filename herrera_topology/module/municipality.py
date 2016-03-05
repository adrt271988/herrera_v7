#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################

from osv import osv
from osv import fields
from tools.translate import _

class Municipality(osv.osv):
    '''
    Model added to manipulate separately the municipalities on Partner address.
    '''
    _description='Model to manipulate Municipalities'
    _name ='res.municipality'
    _columns = {
        'name': fields.char('Municipality Name', size=64, required=True,help="In this field enter the name of the Municipality\n"),
        'code': fields.char('Municipalities Code', size=3,help='The municipality code in three numbers, Example: 001 for Libertador .\n', required=True),
        'state_id': fields.many2one('res.country.state', 'State', required=True , help="In this field enter the name of the state to which the municipality is associated \n"),
        'parish_ids':fields.one2many('res.parish','municipalities_id','Parish',required=True, help="In this field enter the name of the parishes of municipality \n"),
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

Municipality()

