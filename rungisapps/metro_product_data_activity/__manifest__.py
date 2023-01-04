{
    'name': 'Product Collection Data Activity',
    'version': '12.0.1.0.0',
    'summary': 'EMO-2.4 Set activity for collecting new product data',
    'category': 'Inventory',
    'author': 'Thore Baden, Hucke Media GmbH & Co. KG',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'mail',
        'stock',
    ],
    'data': [
        'views/product_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
