# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _

class validate_all_account_move(osv.osv_memory):
    
    _name = "validate.account.all.move"
    _description = "Asentar todo"
    _columns = {
                'sure': fields.boolean('Marque si esta seguro que desea continuar'),
                'options': fields.selection([('0','Asentar todos los comprobantes de un periodo'),
                                             ('1','Asentar todos los comprobantes')], 'Seleccione', required=True, select=True),
                'period_id': fields.many2one('account.period', 'Periodo', domain=[('state','<>','done')]),
    }

    def validate_move_all(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        if data.options == '0':
            ids_move = obj_move.search(cr, uid, [('state','=','draft'),('period_id','=',data.period_id.id)])
        elif data.options == '1':
            ids_move = obj_move.search(cr, uid, [('state','=','draft')])
        if not ids_move:
            raise osv.except_osv(_('Warning!'), _('Verifique que tenga asientos en borrador.'))
        obj_move.button_validate(cr, uid, ids_move, context=context)
        return {'type': 'ir.actions.act_window_close'}

validate_all_account_move()
