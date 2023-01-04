# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
{
    'name': 'CatchWeight - Ecommerce',
    'version': '12.0.2.0.5',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'Catch Weight e-commerce',
    'description': """
    Catch Weight management in e commerce
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'license': 'Other proprietary',
    'depends': [
       'tis_catch_weight',
        'website_sale'
    ],
    'data': [
        'views/templates.xml',
        'views/sale_product_configurator_templates.xml'
    ],
    'qweb': ['static/src/xml/website_sale_dashboard_cw.xml'],
    'installable': True,
    'auto_install': False,
    'application': True
}

