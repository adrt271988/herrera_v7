# -*- encoding: utf-8 -*-
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp
import time


class inherited_fiscal_book(orm.Model):
    """
    Adecuaciones de los libros de compra y venta para Herrera C.A
    """
    _inherit = "fiscal.book"

    _columns = {   }
    
    def get_doc_type(self, cr, uid, inv_id=None, iwdl_id=None, cf_id=None,fb_id=None, context=None):
        """ Devuelve una cadena que indica el tipo de documento. Para retenciones devuelve 'AJST' 
        y para los documentos de factura devuelve valores diferentes dependiendo del tipo de factura: 
        Nota de Débito 'N / DE ", Nota de Crédito' N / CR ', Factura" FACT".. Esta funcion Fue heredada 
        y modificada para que devuelva 1 por factura, 2 por ND y 3 por NC.
        @parametro inv_id : invoice id
        @parametro iwdl_id: wh iva line id
        """
        context = context or {}
        res = False
        if fb_id:
            obj_fb = self.pool.get('fiscal.book')
            fb_brw = obj_fb.browse(cr, uid, fb_id, context=context)
        if inv_id:
            inv_obj = self.pool.get('account.invoice')
            inv_brw = inv_obj.browse(cr, uid, inv_id, context=context)
            if (inv_brw.type in ["out_invoice"] and inv_brw.parent_id) \
                    or inv_brw.type in ["in_refund"]:
                res = "3"
            elif (inv_brw.type in ["in_invoice"] and inv_brw.parent_id) or \
                    inv_brw.type in ["out_refund"]:
                res = "2"
            elif inv_brw.type in ["in_invoice", "out_invoice"]:
                res = "1"

            assert res, str(inv_brw) + ": Error in the definition \
            of the document type. \n There is not type category definied for \
            your invoice."
        elif iwdl_id:
            res = 'AJST' if fb_id and fb_brw.type == 'sale' else 'RET'
        elif cf_id:
            res = 'F/IMP'

        return res

    def link_book_lines_and_taxes(self, cr, uid, fb_id, context=None):
        """ Herencia: Agregada condicion para que sume los totales de los impuestos Padre.
            Actualiza los impuestos de libros fiscales. Vincular el impuesto con la correspondiente 
            línea del libro y actualización de los campos de impuestos de suma en el libro. 
            @param fb_id: el id de la actual cartera fiscal """
        
        context = context or {}
        fbl_obj = self.pool.get('fiscal.book.line')
        #~ write book taxes
        data = []
        for fbl in self.browse(cr, uid, fb_id, context=context).fbl_ids:
            if fbl.invoice_id:
                sign = 1 if fbl.doc_type != 'N/CR' else -1
                amount_field_data = \
                    { 'total_with_iva': fbl.invoice_id.amount_untaxed * sign,
                      'vat_sdcf': 0.0, 'vat_exempt': 0.0 }
                taxes = fbl.type in ['im','ex'] \
                    and fbl.invoice_id.imex_tax_line \
                    or fbl.invoice_id.tax_line
                for ait in taxes:
                    if ait.tax_id and not ait.tax_id.parent_id: #condicion agregada
                        data.append((0, 0, {'fb_id': fb_id,
                                            'fbl_id': fbl.id,
                                            'ait_id': ait.id}))
                        amount_field_data['total_with_iva'] += ait.tax_amount * sign
                        if ait.tax_id.appl_type == 'sdcf':
                            amount_field_data['vat_sdcf'] += ait.base_amount * sign
                        if ait.tax_id.appl_type == 'exento':
                            amount_field_data['vat_exempt'] += ait.base_amount * sign
                    else:
                        data.append((0, 0, {'fb_id':
                                    fb_id, 'fbl_id': False, 'ait_id': ait.id}))
                fbl_obj.write(cr, uid, fbl.id, amount_field_data, context=context)

        if data:
            self.write(cr, uid, fb_id, {'fbt_ids': data}, context=context)
        self.update_book_taxes_summary(cr, uid, fb_id, context=context)
        self.update_book_lines_taxes_fields(cr, uid, fb_id, context=context)
        self.update_book_taxes_amount_fields(cr, uid, fb_id, context=context)
        self.update_book_additional_values(cr, uid, fb_id, context=context)
        return True
    
    def get_transaction_type(self, cr, uid, fb_id, inv_id, context=None):
        """ Método que devuelve el tipo de línea del libro fiscal relacionada con la 
            factura dada por cheking el formulario de aduanas asociado y el fiscal 
            tipo de libro.
        @param fb_id: fiscal book id
        @param inv_id: invoice id
        """
        context = context or {}
        inv_obj = self.pool.get('account.invoice')
        rp_obj = self.pool.get('res.partner')
        inv_brw = inv_obj.browse(cr, uid, inv_id, context=context)
        rp_id =  rp_obj._find_accounting_partner(inv_brw.partner_id)
        rp_brw = rp_obj.browse(cr, uid, rp_id, context=context)
        fb_brw = self.browse(cr, uid, fb_id, context=context)
        if rp_brw.partner_type == 'IMP':
            return 'im'
        else:
            return 'do'

    
    def update_book_additional_values(self, cr, uid, fb_id, context=None):

        fbl_obj = self.pool.get('fiscal.book.line')
        idss = fbl_obj.search(cr, uid, [('fb_id', '=', fb_id)], context=context)
        for fb_line in fbl_obj.browse(cr, uid, idss, context=context):
            if fb_line.invoice_id:
                fbl_obj.write(cr, uid, fb_line.id, {'shop_code':fb_line.invoice_id.partner_id.shop_id.code }, context=context)
                
                if (fb_line.invoice_id.type in ["out_invoice"] and fb_line.invoice_id.parent_id) or fb_line.invoice_id.type in ["in_refund"]:
                    fbl_obj.write(cr, uid, fb_line.id, {'nc_number':fb_line.invoice_id.number }, context=context)
               
                elif (fb_line.invoice_id.type in ["in_invoice"] and fb_line.invoice_id.parent_id) or fb_line.invoice_id.type in ["out_refund"]:
                    fbl_obj.write(cr, uid, fb_line.id, {'nd_number':fb_line.invoice_id.number }, context=context)
        return True
        
inherited_fiscal_book()



class inherited_fiscal_book_lines(orm.Model):

    _inherit = "fiscal.book.line"

    _columns = {  'shop_code': fields.char('S', size=1),
                  'nd_number': fields.char(string='Número N/D', size=32,help='Número de la nota de débito'),
                  'nc_number': fields.char(string='Número N/C', size=32,help='Número de la nota de crédito'),
                  'form_imex': fields.char(string='Número Planilla (C80 o C81)', size=32,help='Número de la planilla de importación'),
                  'imex_number': fields.char(string='Número Exp.Imp', size=32,help='Número de Importación'),
                  'type': fields.selection( [('im', 'IMPORT'),
                                             ('do', 'NAC'),
                                             ('ex', 'EXPORT'),
                                             ('tp', 'Tax Payer'),
                                             ('ntp', 'Non-Tax Payer')],
                                            string = 'Tipo Prov', required=True,
                                            help="Book line transtaction type:" \
                                            " - Purchase: Import or Domestic." \
                                            " - Sales: Expertation, Tax Payer, Non-Tax Payer."),
                }
        
inherited_fiscal_book_lines()


class inherited_res_partner(osv.osv):

    _inherit = "res.partner"

    _columns = {  
                'partner_type': fields.selection([('NAC', 'Nacional'),
                                                  ('IMP', 'Internacional')], string='Tipo'),
                }
        
inherited_fiscal_book_lines()
