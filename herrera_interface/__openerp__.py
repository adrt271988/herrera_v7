{
    'name': 'Interfaces para la entrada/salida de data de Herrera C.A.',
    'version': '1.0',
    'category': 'Sales',
    'description': """
Este modulo contiene las interfaces para integrar la data OpenERP con la data proveniente de equipos moviles.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ['herrera_sales_planning','herrera_product'],
    'data': [
        'wizard/import_data.xml',
        'view/res_config_view.xml',
        'view/interface_view.xml',
        ],
    'demo': [],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
