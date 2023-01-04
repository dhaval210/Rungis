# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Product Average Quantity',
    'version': '12.0.2.1.1',
    'category': 'Inventory',
    'summary': 'Catchw8 - Average catch weight quantity for products',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 199,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
    Average catch weight quantity for products in sales, purchase, invoice, picking etc.
    """,
    'depends': [
	'tis_catch_weight'
	],
    'data': [
        'security/catch_weight_security.xml',
        'views/product_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
