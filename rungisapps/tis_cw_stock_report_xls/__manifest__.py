# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight - Stock Report',
    'version': '12.0.2.0.3',
    'category': 'Sales',
    'sequence': 1,
    'author': 'Technaureus Info Solutions',
    'summary': 'Catch Weight Stock report excel',
    'website': 'http://www.catchweighterp.com/',
    'description': """Catch Weight Stock report excel
""",
    'depends': ['tis_catch_weight', 'report_xlsx'],
    'data': [
        'report/cw_stock_report.xml',
        'wizard/stock_quantity_history.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
