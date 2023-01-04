{
    'name': 'Metro Order Grid Cache Purchase Schedule',
    'version': '12.0.1.0.1',
    'summary': 'RUN-988',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-988
    ''',
    'category': 'Tool',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'metro_cache_order_grid',
        'metro_purchase_schedule',
    ],
    'data': [
        'views/cache_order_grid.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
