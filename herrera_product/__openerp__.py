
{
    "name": "Productos Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Products",
    "description": """
     Este modulo contiene las adaptaciones en la ficha de Productos para HERRERA, C.A
    """,
    'images': [],
    'depends': ['purchase','product_historical_price','product_visible_discount'],
    'init_xml': [],
    'data': [
            'security/product_security.xml',
            'data/res_users_data.xml',
            'data/product_sica_data.xml',
            'data/uom_data.xml',
            'data/product_data.xml',
            #~ 'data/supplierinfo_data.xml',
            'data/pricelist_data.xml',
            ],
    'update_xml': [
        'view/product_view.xml',
        'view/product_sica_view.xml',
        #~ 'view/product_classifications.xml',
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
