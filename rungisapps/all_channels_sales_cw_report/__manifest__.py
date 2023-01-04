# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>)
{
    'name': 'CatchWeight - All Channels Sales Report',
    'version': '12.0.2.0.4',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'Catchw8 - Catch weight analysis report for all channels sales order',
    'description': """
    Catch weight analysis report for all channels sales order
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 99,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'tis_catch_weight',
    ],
    'data': [
        'report/report_all_channels_views.xml'
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True
}
