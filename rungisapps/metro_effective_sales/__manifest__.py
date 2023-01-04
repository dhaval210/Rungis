# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Effective Sales on SO-Line',
    'summary': 'EMO-498',
    'description': """
EMO-498: New reporting view to represent the "effective Sales". Adds a menu entry for SO-Lines, 
adds the field "Effective Sales" on the SO-Line,
adds a reporting view on the SO-Line.
        """,
    'author': 'Odoo SA',
    'version': '0.1',
    'module': 'Metro',
    'depends': [
        'sale',
        'sales_team',
        'metro_customer_family',
    ],
    'data': [
        'views/sale_order_line_views.xml',
    ],
    'installable': True,
}
