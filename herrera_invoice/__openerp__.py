
{
    "name": "Facturas Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Contabilidad",
    "description": """
     Este modulo contiene las adaptaciones en la facturacion de pedidos de compras para HERRERA, C.A
    """,
    'images': [],
    'depends': ['account','purchase','l10n_ve_fiscal_requirements','herrera_company'],
    'init_xml': [],
    'update_xml': [
            'view/invoice_view.xml',
            'wizard/invoice_control_number_view.xml',
            'wizard/reopen_lot_view.xml',
            'view/invoice_lot_view.xml',
            'view/invoice_motive_view.xml',
            ],
    'data': [
        'report/reports.xml',
        'data/sequence.xml',
        ],    
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
