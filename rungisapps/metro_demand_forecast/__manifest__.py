{
    'name': 'Metro Demand Forecast',
    'version': '12.0.1.0.2',
    'summary': 'RUN-894',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-894
    ''',
    'category': 'Inventory',
    'author': 'Thore Baden, Hucke Media GmbH & Co. KG',
    'website': 'https://www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'sale',
        'purchase',
        'metro_db2_connector',
    ],
    'data': [
        'reports/report_stock_demand_forecast.xml',
        'security/ir.model.access.csv',
        'views/product_product.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
