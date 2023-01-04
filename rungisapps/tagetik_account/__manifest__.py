# -*- coding: utf-8 -*-
{
    'name': "Tagetik Account",

    'summary': """
        Add Tagetik Account in Chart of Account""",

    'description': """
       Add Tagetik Account in Chart of Account
    """,

    'author': "Nisu Technology",
    'website': "http://nisu.technology/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
