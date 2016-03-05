
{
    "name": "Activos Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "Activos",
    "description": """
     Este modulo contiene las adaptaciones en el modulo de Activos para HERRERA, C.A
    """,
    'images': [],
    'depends': ['account_asset','sale','herrera_hr'],
    'init_xml': [],
    'update_xml': [
    'reports.xml',
    'view/asset_view.xml',
    'view/category_view.xml',
    'view/inventory_view.xml',
    'wizard/asset_depreciate_view.xml',
    'wizard/asset_report_view.xml',
    'wizard/inventory_line_view.xml',
    'wizard/confirm.xml',
    ],
    'data': [
    #~ 'data/categories.xml',
    #~ 'data/asset_data.xml'
    ],    
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
