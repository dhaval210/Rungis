{
    'name': 'Metro Order Grid Cache Stock Data',
    'version': '12.0.1.0.6',
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
        'stock',
        'queue_job',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cache_order_grid.xml',
        'views/res_config_settings.xml',
        'views/res_generic_warehouse.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
