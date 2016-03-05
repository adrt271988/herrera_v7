# -*- coding: utf-8 -*-
import logging
import openerp.netsvc as netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _

class wizard_import_process(osv.osv_memory):
    
    _name = 'wizard.import.process'
    _columns = {
                'pb_lines': fields.one2many('lines.wizard.import.process', 'wizard_id', 'Lineas'),
               }

    def action_add(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        wl_obj = self.pool.get('lines.wizard.import.process')
        fbl_obj = self.pool.get('fiscal.book.line')
        
        wlids = wl_obj.search(cr, uid, [('wizard_id', '=', ids[0])], context=context)
        
        for line in wl_obj.browse(cr, uid, wlids):
            fbl_obj.write(cr, uid, line.fb_line.id, {'form_imex': line.form_imex,'imex_number': line.imex_number }, context=context)
        return True

wizard_import_process()


class lines_wizard_import_process(osv.osv_memory):
    
    _name = 'lines.wizard.import.process'
    _columns = { 
                'wizard_id': fields.many2one('wizard.import.process', 'Lineas', required=True),
                'fb_line': fields.many2one('fiscal.book.line', 'Número de Control', required=True),
                'form_imex': fields.char(string='Número Planilla (C80 o C81)', size=32,help='Número de la planilla de importación'),
                'imex_number': fields.char(string='Número Exp.Imp', size=32, help='Número de Importación'),
               }
lines_wizard_import_process()
