{
    'name': 'Customers Status',
    'version': '12.0.1.0.1',
    'summary': ' EMO-1066 ''EMO-1067''EMO-1068',
    'description': 'EMO-1066:This module allows to get New Customer '
                   'EMO-1067:Get Buying Customer '
                   'EMO-1068:Get Lost Customer ',

    'author': ' Odoo PDA',
    'category': 'Contacts',
    'depends': [
        'contacts',
        'sale_management',
        'account',
        ],
    'data': [
        'views/customer_status_view.xml',
        'views/sale_invoice_status.xml',
        'views/view_pivot.xml',


    ],
    'license': 'LGPL-3',
    'installable': True,
}