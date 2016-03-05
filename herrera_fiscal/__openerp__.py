{
    "name": "Libros Fiscales Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Contabilidad",
    "description": """
     Este modulo contiene las adaptaciones del modulo ve_fiscal_book de openerp-venezuela-localization para HERRERA, C.A
    """,
    'images': [],
    'depends': ['l10n_ve_fiscal_book'],
    'data': [],
    'init_xml': [],
    'update_xml': ['view/fiscal_book_view.xml',
                   'report/fiscal_book_report.xml'
                   ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
