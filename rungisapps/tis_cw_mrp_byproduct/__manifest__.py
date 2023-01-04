# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Manufacturing Byproduct',
    'version': '12.0.2.0.4',
    'category': 'Manufacturing',
    'summary': 'Catchw8 - Catch weight Manufacturing Byproduct',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 149,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
    Catch weight Manufacturing(MRP) Byproduct
    """,
    'depends': [
	'mrp_byproduct',
	'tis_cw_mrp'
	],
    'data': [
        'views/mrp_bom_views.xml'
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': ['static/src/xml/mrp.xml'],
}

