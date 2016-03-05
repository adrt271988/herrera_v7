{
    'name': 'Clientes/Proveedores Herrera C.A.',
    'version': '1.0',
    'category': 'Partners',
    'description': """
Este modulo contiene las adaptaciones del modulo de partner de OpenERP (res.partner) para HERRERA, C.A.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ["account","sale","base_vat","l10n_ve_fiscal_requirements","herrera_topology","herrera_company","herrera_warehouse","herrera_distribution"],
    'data': [
        #~ 'data/partners_data.xml',
    ],
    'demo': [],
    'update_xml' : [
        'view/partner_view.xml'
    ],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
