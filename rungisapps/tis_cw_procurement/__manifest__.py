# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Procurement, Replenish',
    'version': '12.0.2.1.3',
    'category': 'Inventory',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'summary': 'Catchw8 - Catch Weight Procurement rules and Replenish',
    'website': 'http://www.catchweighterp.com/',
    'price': 99,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
    Catch Weight Procurement rules
""",
    'depends': [
        'tis_catch_weight',
        'tis_cw_average_qty'
    ],
    'data': [
        'views/stock_views.xml',
        'wizard/product_replenish_views.xml'
    ],
    'demo': [
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
