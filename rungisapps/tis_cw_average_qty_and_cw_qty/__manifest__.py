# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Product Average Quantity & CW Quantity',
    'version': '12.0.2.0.4',
    'category': 'Product',
    'summary': 'Average catch weight quantity and cw quantity in purchase',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'description': """
    Average catch weight quantity and cw quantity in purchase
    """,
    'depends': ['tis_cw_average_qty'],
    'data': [
        'views/purchase_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
