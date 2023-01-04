# -*- coding: utf-8 -*-
# Part of Synconics. See LICENSE file for full copyright and licensing details.

{
    'name': "Stock Ageing Analysis",
    'version': '1.0',
    'category': 'Warehouse',
    'summary': 'Stock Ageing Analysis PDF and Excel Report',
    'description': """
    Stock Ageing Analysis PDF and Excel Report
    """,
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'depends': ['sale_management', 'sale_stock', 'purchase'],
    'data': [
        'wizard/stock_ageing_view.xml',
        'report/stock_ageing_report.xml',
    ],
    'images': [
        'static/description/main_screen.jpg',
    ],
    'price': 35,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
}