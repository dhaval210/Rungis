{
    'name': 'Default Accounts per Partner Type - Metro Systems',
    'summary': 'EMO-254: Default Accounts per Partner Type',
    'description': """
======================================
        """,
    'author': 'Odoo PDA',
    'version': '0.3',
    'depends': [
        'sale',
        'account',
    ],
    'data': [
        'views/account_views.xml',
        'views/default_accounts_partner_type.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
