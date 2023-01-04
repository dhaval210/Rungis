# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt. Ltd.(<http://technaureus.com/>).
{
    'name': 'CatchWeight - Average Quantity Ecommerce',
    'version': '12.0.2.0.5',
    'sequence': 1,
    'category': 'Product',
    'summary': 'Average Catch Weight Quantity in  e commerce',
    'description': """
    Average Catch Weight Quantity in  e-commerce
""",
    'author': 'Technaureus Info Solutions Pvt Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'license': 'Other proprietary',
    'depends': [
       'tis_cw_web_sale',
        'tis_cw_average_qty'
    ],
    'data': [
        'views/assets.xml',
        'views/templates.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

