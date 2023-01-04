# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Batch Picking',
    'version': '12.0.0.0.0',
    'sequence': 1,
    'category': 'Inventory',
    'summary': 'Catchw8 - This module adds the batch picking option in warehouse management with CW8',
    'description': """
    This module adds the batch picking option in warehouse management with CW8
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'stock_picking_batch',
        'tis_catch_weight'
    ],
    'data': [
        'report/report_picking_batch.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True

}
