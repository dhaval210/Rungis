{
    'name': 'Package Barcode',
    'version': '12.0.1.1.5',
    'summary': 'Assign Barcodes to Packages',
    'category': 'Inventory',
    'author': 'Thore Baden, Hucke Media GmbH & Co. KG',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'metro_app_picking_enhancement',
    ],
    'data': [
        'views/stock_quant_package.xml',
    ],
    'installable': True,
    'application': False,
}
