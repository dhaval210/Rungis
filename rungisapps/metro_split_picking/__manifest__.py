{
    'name': 'Metro Split Picking',
    'version': '12.0.1.2.4',
    'author': 'Hucke Media GmbH & Co. KG',
    'category': 'Custom',
    'website': 'https://www.hucke-media.de/',
    'licence': 'AGPL-3',
    'summary': 'Split Picking',
    'depends': [
        'delivery',
        'stock'
    ],
    'data': [
        'data/decimal_precision.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'views/product_category_view.xml',
        'views/product_template_view.xml',
        'views/stock_location_view.xml',
        'views/stock_picking_type_view.xml',
        'views/stock_warehouse_view.xml',
        'views/transport_unit_view.xml',
    ],

    'installable': True,
    'application': False,
}
