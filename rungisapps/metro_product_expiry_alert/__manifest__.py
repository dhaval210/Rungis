{
    'name': 'Produt Expiry Alert',
    'version': '12.0.1.0.2',
    'summary': ' EMO-1119 ',
    'description': """EMO-1119:a horizontal extension to the  module 
    product_expiry_alert Send alert mail to responsible person 
    consolidating all lots for a product, Added purchasing team to 
    Lot/serial number""",

    'author': ' Odoo PDA',
    'category': 'Sales',
    'depends': [
        'base',
        'stock',
        'metro_purchasing_team',
        'product_expiry',
        ],
    'data': [
        'data/data.xml',
        'views/stock_view.xml',
        'views/templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}