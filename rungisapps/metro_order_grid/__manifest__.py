{
    'name': 'Metro Order Grid',
    'version': '12.0.1.0.9',
    'summary': 'RUN-988',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-988
    ''',
    'category': 'Tool',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'metro_cache_order_grid_stock',
        'metro_cache_order_grid_sale',
        'metro_cache_order_grid_purchase',
        'metro_cache_order_grid_purchase_schedule',
        'purchase',
        'sale',
    ],
    'data': [
        'views/cache_order_grid.xml',
        'views/product_category.xml',
        'views/purchase_order.xml',
        'views/product_supplierinfo.xml',
        'views/sale_order_line.xml',
        'views/stock_quant.xml',
        'wizard/order_grid_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
