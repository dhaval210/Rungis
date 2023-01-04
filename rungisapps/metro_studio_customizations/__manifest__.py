# -*- coding: utf-8 -*-
{
    'name': "METRO Studio Customizations",
    'description': """
        This module contains METRO specific customizations for Odoo.
    """,

    'author': "Odoo PDA",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Metro',
    'version': '12.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        "product",
        "sale"
    ],

    # always loaded
    'data': [
        "views/product_template.xml",
        "views/res_partner.xml",
        "views/res_users.xml",
    ],
    # only loaded in demonstration mode
    'demo': [],
}