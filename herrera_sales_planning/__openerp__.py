{
    'name': 'Planificación de Ventas - Herrera C.A.',
    'version': '1.0',
    'category': 'Sales',
    'description': """
Este modulo contiene las adaptaciones del modulo de CRM(crm) & Ventas(sales) de OpenERP para HERRERA, C.A. Incluye equipo de ventas, rutas, presupuesto de venta entre otros.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ['herrera_sales', 'herrera_partner'],
    'data': [
        'data/categ_data.xml',
        'data/ir.model.access.csv',
        'view/users_view.xml',
        'view/sale_plan_view.xml',
        'view/partner_view.xml',
        ],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
