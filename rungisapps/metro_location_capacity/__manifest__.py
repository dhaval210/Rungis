# -*- coding: utf-8 -*-

{
    'name': 'Metro Location Capacity',
    'version': '12.0.1.0.4',
    'summary': ' EMO-1129 ',
    'description': """EMO-1129:Location Capacity""",
    'author': ' Odoo PDA',
    'category': 'warehouse',
    'depends': [
        'stock',
        'purchase',
        'metro_putaway_strategy'
    ],
    "data": [
        'views/stock_location_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
