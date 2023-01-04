# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Manufacturing',
    'version': '12.0.2.3.3',
    'category': 'Manufacturing',
    'summary': 'Catchw8 - Catch weight Manufacturing(MRP)',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 770,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
    Catch weight Manufacturing(MRP)
    """,
    'depends': [
	'tis_catch_weight', 
	'mrp'
	],
    'data': [
        'views/product_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_unbuild_views.xml',
        'views/mrp_workorder_views.xml',
        'views/stock_move_views.xml',
        'wizard/mrp_product_produce_views.xml',
        'wizard/stock_warn_insufficient_qty_views.xml',
        'report/mrp_report_bom_structure.xml',
        'report/mrp_production_templates.xml',

    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': ['static/src/xml/mrp.xml'],
}
