{
    "name": "Pagos y comprobantes Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Contabilidad",
    "description": """
     Este modulo contiene las adaptaciones de los modulos de pago y comprobantes de pago para HERRERA, C.A
    """,
    'images': [],
    'depends': ['account_voucher','account_payment','l10n_ve_fiscal_book'],
    'data': [
            'view/payment_order_view.xml',
            'view/bank_checkbook_view.xml',
            'wizard/invoice_payment_supplier_view.xml',
            'wizard/pay_planning_view.xml',
            'wizard/account_payment_wizard_view.xml',
            'report/reports.xml',
            'data/sequence.xml',
            'view/account_invoice_view.xml',
            'wizard/account_returned_checks_view.xml',
            ],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
