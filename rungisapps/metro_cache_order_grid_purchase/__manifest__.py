{
    'name': 'Metro Order Grid Cache Purchase',
    'version': '12.0.1.0.2',
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
        'purchase',
    ],
    'data': [
        'views/cache_order_grid.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
