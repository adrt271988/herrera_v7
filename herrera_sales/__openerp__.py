{
    "name": "Ventas Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Ventas",
    "description": """
     Este modulo contiene las adaptaciones en el modulo de ventas para HERRERA, C.A
    """,
    'images': [],
    'depends': ['sale','account','herrera_product','stock','sale_stock','herrera_mail'],
    'data': [
        'data/sales_data.xml',
        'data/swift_code_banks.xml',
        'data/journals.xml',
        #'data/pricelist.xml,'
        'data/sale_workflow.xml',
        'view/sale_shop.xml',
        'view/mail_view.xml',
        'view/sale_view.xml',
        'wizard/massive_stock_analysis.xml',
        'report/sales_report.xml',
        'view/account_journal_view.xml',
    ],
    'init_xml': [],
    'update_xml': [
        
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
