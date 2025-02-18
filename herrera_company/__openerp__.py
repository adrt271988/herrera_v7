{
    'name': 'Datos de la compañia Herrera C.A.',
    'version': '1.0',
    'category': 'Company',
    'description': """
Este modulo contiene las adaptaciones del modulo de compañia de OpenERP (res.company) para HERRERA, C.A.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ["base", "base_vat","l10n_ve_fiscal_requirements","herrera_topology", "product"],
    'data': [
        'data/res_company_data.xml',
        'data/pricelist_data.xml',
        'data/res_lang_data.xml',
    ],
    'demo': [],
    'update_xml' : [
        'view/res_company_view.xml'
    ],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
