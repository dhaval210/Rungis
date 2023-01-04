{
    'name': 'Metro block exceeding Qty',
    'version': '12.0.1.0.1',
    'summary': '''
        RUN-346
    ''',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-346
    ''',
    'category': 'Enhancement',
    'author': '''
        Thore Baden, Huckemedia GmbH & Co. KG,
    ''',
    'website': 'https://www.hucke-media.de/',
    'license': 'LGPL-3',
    'depends': [
        'stock',
    ],
    'data': [
        'data/res_config_settings_data.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
