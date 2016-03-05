{
    "name": "Compras Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Compras",
    "description": """
     Este modulo contiene las adaptaciones en el modulo de compras para HERRERA, C.A
    """,
    'images': [],
    'depends': ['purchase','account','herrera_product','stock','purchase_discount','l10n_ve_withholding_iva'],
    'data': [
        'security/purchase_security.xml', 
        'security/ir.model.access.csv', 
        'data/purchase_data.xml', 
        'data/pricelist.xml',
        'data/ir_translation.xml',
        'report/reports.xml',
        'view/purchase_view.xml',
        'view/purchase_pricelist_view.xml',
        'view/pricelist_supplier.xml',
        'view/invoice_view.xml',
        'wizard/pricelist_supplier.xml',
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
