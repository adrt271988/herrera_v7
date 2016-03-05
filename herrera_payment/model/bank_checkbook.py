# -*- encoding: utf-8 -*-
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp
import time


class account_bank_checkbook(osv.osv):
    """
    Chequeras
    """
    _name = "account.bank.checkbook"
    
    def set_to_open(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state':'open' }, context)

    def set_to_close(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state': 'close'}, context=context)

    def set_to_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)
    
    def _get_qty_check(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}

        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            #~ if not line.first_number.isdigit() or not line.last_number.isdigit():
                #~ raise osv.except_osv(_('Warning!'), _('Los campos "Número inicial" y "Número final" deben contener solo números.'))
            res[line.id] = (int(line.last_number) - int(line.first_number)) + 1
        return res
        
    def _get_remaining_check(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        check_obj = self.pool.get('account.bank.check')
                
        for line in self.browse(cr, uid, ids, context=context):
            #~ if not line.first_number.isdigit() or not line.last_number.isdigit():
                #~ raise osv.except_osv(_('Warning!'), _('Los campos "Número inicial" y "Número final" deben contener solo números.'))
            qty = (int(line.last_number) - int(line.first_number)) + 1
            posted_ids = check_obj.search(cr, uid, [('checkbook_id','=', line.id),('check_check','=', True)])
            if posted_ids: 
                qty = qty - len(posted_ids)
            res[line.id] = qty
        return res
        
    _columns = {
                'name': fields.char('Chequera', size=24, required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'reference': fields.char('Referencia', size=12, required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'first_number': fields.char('Número inicial', required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'last_number': fields.char('Número final', required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'qty_checks': fields.function(_get_qty_check, method=True, type='integer', string='Cantidad de Cheques', store=True),
                'remaining_checks': fields.function(_get_remaining_check, method=True, type='integer', string='Cheques restantes'),
                'account_bank_id': fields.many2one('res.partner.bank','Cuenta Bancaria', required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'check_ids': fields.one2many('account.bank.check', 'checkbook_id', 'Cheques'),
                'state': fields.selection([('draft','Borrador'),('open','En uso'),('done','Terminada'),('close','Cancelada')], 'Status',required=True),
                'date': fields.date('Fecha', readonly=True, states={'draft':[('readonly',False)]}),
                'user_id': fields.many2one('res.users', 'User', readonly=True),
               }
    _defaults = {
                'name' :  lambda self,cr,uid,c: self.pool.get('ir.sequence').get(cr, uid, 'account.bank.checkbook',context=c),
                'date': lambda self, cr, uid, context: time.strftime('%Y-%m-%d'),
                'state': 'draft',
                'user_id': lambda self, cr, uid, ctx: uid
                }
    
    def generate_checks(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        check_obj = self.pool.get('account.bank.check')
        posted_ids = check_obj.search(cr, uid, [('checkbook_id','=', ids[0])])
        data = self.browse(cr, uid, ids, context=context)[0]
        first_number = data.first_number
        last_number = data.last_number
        if first_number.isdigit() and last_number.isdigit():
            first_number = int(first_number)
            last_number  = int(last_number)
        else:
            raise osv.except_osv(_('Warning!'), _('Los campos "Número inicial" y "Número final" deben contener solo números. Por favor verifique.!'))
        if last_number < first_number:
            raise osv.except_osv(_('Warning!'), _('EL número del ultimo cheque debe ser mayor o igual al número del primer cheque..'))
        
        qty = (last_number - first_number) + 1
        qty_old = len(posted_ids)
        if posted_ids:
            if qty_old == qty:
                for i in posted_ids:
                    check_obj.write(cr, uid, i, {'number': first_number}, context=context)
                    first_number +=1
            elif qty_old > qty:
                dif = qty_old - qty
                for k in range(dif):
                    val= posted_ids.pop(k)
                    check_obj.unlink(cr, uid, [val], context=context)
                for i in posted_ids:
                    check_obj.write(cr, uid, i, {'number': first_number}, context=context)
                    first_number +=1
            elif qty_old < qty:
                dif = qty - qty_old
                for i in posted_ids:
                    check_obj.write(cr, uid, i, {'number': first_number}, context=context)
                    first_number +=1
                for k in range(dif):
                    vals = { 'number': first_number , 'checkbook_id':ids[0] }
                    check_obj.create(cr, uid, vals, context=context)
                    first_number +=1
        else:
            while first_number <= last_number:
                vals = { 'number': first_number , 'checkbook_id':ids[0] }
                check_obj.create(cr, uid, vals, context=context)
                first_number +=1
        return True

account_bank_checkbook()

class account_bank_check(osv.osv):
    """
    Cheques
    """
    _name = "account.bank.check"
    
    def _get_check_check(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = bool(line.move_id)
        return res
    
    def _get_children_check(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        check_obj = self.pool.get('account.bank.check')
        checkbook = self.browse(cr, uid, ids, context=context)[0]
        posted_check_ids = check_obj.search(cr, uid, [('checkbook_id','=', ids[0]),('check_check','=', True)])
        qty = (checkbook.last_number - checkbook.first_number) + 1
        if posted_check_ids: 
            qty = qty - len(posted_check_ids)
        return {ids[0]: qty}
        
    _columns = {
                'name': fields.char('Descripción', size=50),
                'number': fields.char('Número', size=20, required=True),
                'amount': fields.float('Monto'),
                'bank_id': fields.many2one('res.bank','Banco'),
                'checkbook_id': fields.many2one('account.bank.checkbook','Chequera', required=True),
                'partner_id': fields.many2one('res.partner', 'Beneficiario'),
                'date_use': fields.date('Fecha de Uso'),
                'move_id': fields.many2one('account.move', 'Asiento'),
                'check_check': fields.function(_get_check_check, method=True, type='boolean', string='Usado', store=True),
                'parent_state': fields.related('checkbook_id', 'state', type='char', string='Status de Chequera'),
               }
    _defaults = {
                #~ 'name' :  lambda self, cr, uid, c: self.pool.get('ir.sequence').get(cr, uid, 'account.bank.checkbook',context=c),
                
                }


account_bank_check()
