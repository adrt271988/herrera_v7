#~ # -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

__TYPES__ =[('sale', 'Sale'),
        ('sale_refund','Sale Refund'), 
        ('purchase', 'Purchase'), 
        ('purchase_refund','Purchase Refund'), 
        ('cash', 'Cash'), 
        ('bank', 'Bank and Cheques'), 
        ('general', 'General'), 
        ('situation', 'Opening/Closing Situation'),
        ('sale_debit', 'Sale Debit'),
        ('purchase_debit', 'Purchase Debit'),
        ('iva_sale', 'Sale Wh VAT'), 
        ('iva_purchase', 'Purchase Wh VAT'), 
        ('islr_purchase', 'Purchase Wh Income'), 
        ('islr_sale', 'Sale Wh Income'), 
        ('mun_sale', 'Sale Wh County'), 
        ('mun_purchase', 'Purchase Wh County'),
        ('src_sale', 'Sale Wh src'), 
        ('src_purchase', 'Purchase Wh src'),
        ('sale_dpp', 'DPP Ventas'),
        ('dpp_recovery', 'DPP IVA Recuperacion'),
	]

class inherited_account_journal(osv.osv):

    _inherit = 'account.journal'
        
    _columns = {
       'shop_id': fields.many2one('sale.shop', 'Sucursal'),
       'type': fields.selection(__TYPES__,  'Type', size=32, required=True, 
						help =  "Select 'Sale' for customer invoices journals."\
						    " Select 'Purchase' for supplier invoices journals."\
						    " Select 'Cash' or 'Bank' for journals that are used in customer or supplier payments."\
						    " Select 'General' for miscellaneous operations journals."\
						    " Select 'Opening/Closing Situation' for entries generated for new fiscal years."\
						    " Select 'Sale Debit' for customer debit note journals."\
						    " Select 'Purchase Debit' for supplier debit note journals."\
						    " Select 'Sale Wh VAT' for customer vat withholding journals."\
						    " Select 'Purchase Wh VAT' for supplier vat withholding journals."\
						    " Select 'Sale Wh Income' for customer income withholding journals."\
						    " Select 'Purchase Wh Income' for supplier income withholding journals."\
						    " Select 'Sale Wh County' for customer municipal withholding journals."\
						    " Select 'Purchase Wh County' for supplier municipal withholding journals."\
						    " Select 'Sale Wh SRC' for customer social withholding journals."\
						    " Select 'Purchase Wh SRC' for supplier social withholding journals."\
						    " Seleccione 'DPP Ventas' para Diario de Descuento Pronto Pago de Ventas."\
						    " Seleccione 'DPP Iva Recuperacion' para Diario de DPP de Recuperacion de IVA."\
						    ),
   }

inherited_account_journal()
