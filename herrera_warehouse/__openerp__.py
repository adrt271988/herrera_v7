{
    'name': 'Logistica Herrera C.A.',
    'version': '1.0',
    'category': 'Warehouse',
    'description': """
Este modulo contiene las adaptaciones del modulo de gestion de almacen de OpenERP (stock) para HERRERA, C.A. Incluyendo inventario, almacenes, ubicaciones, entre otros.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ['base', 'stock', 'sale', 'account', 'purchase','product_expiry'],
    'demo': [],
    'data':['view/stock_production_lot_view.xml',
                  'view/stock_location_view.xml',
                  'view/stock_view.xml',
                  'view/product_expiry_view.xml',
                  'wizard/stock_move_view.xml',
                  'wizard/stock_picking_cancel_view.xml',
                  'wizard/stock_picking_confirm_view.xml',
                  'wizard/stock_partial_picking.xml',
                  'wizard/stock_create_global_view.xml',
                  'view/stock_global_view.xml',
                  'report/stock_report.xml',
                  'data/res_groups_data.xml',
                  'data/ir.model.access.csv',
                  'data/stock_locations.xml',
                  'data/stock_warehouse.xml',
                  'data/sale_shop.xml',
                  'data/res_users_data.xml',
                  'data/sequence.xml',
                  'data/stock_workflow.xml',
                  'view/res_config_view.xml',
    ],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

