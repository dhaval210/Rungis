{
    'name': 'Metro Auto Generate Serial Number',
    'summary': 'EMO-1119',
    'version': '12.0.1.0',
    'description': """EMO-1119 - This modules is used for the  generating
                   serial number on different objects,currently added
                   object :- purchase.order.line """,
    'author': 'METRO',
    'category': 'Purchase',
    'depends': [
        'purchase'
    ],
    'data': [
        'views/purchase_order_line_view.xml',
    ],
    'application': False,
    'license': 'LGPL-3',
    'installable': True,
}