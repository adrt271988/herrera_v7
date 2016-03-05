{
    'name': 'Contabilidad Herrera C.A.',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
Este modulo contiene las adaptaciones del modulo de contabilidad de OpenERP (account.account) para HERRERA, C.A. Incluyendo plan de cuenta, ejercicio fiscal, periodos fiscales, entre otros.
    """,
    'author': 'Herrera C.A.',
    'images': [],
    'depends': ['base','account','sale','l10n_ve_withholding'],
    'data': [
        #'data/accounts.xml',
        #'data/account_data.xml',
        'data/journals.xml',
        #~ 'data/taxes.xml',
        'reports.xml',
        'data/payment_term.xml',
        'data/payment_condition.xml',
        'view/account_move.xml',
        'view/account_voucher.xml',
        'view/withholding_view.xml',
        'view/payment_condition_view.xml',
        'view/res_partner_view.xml',
        'view/taxes_view.xml',
        #~ 'view/product_view.xml',
        'view/account_list.xml',
        'wizard/account_validate_all_move_view.xml',
        'wizard/account_report_balance_view.xml',
        'wizard/account_report_analytical_accounts_view.xml',
    ],
    'demo': [],
    'installable': True,
    'test': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
