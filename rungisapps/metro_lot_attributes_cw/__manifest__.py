{
    'name': 'Metro Lot Attributes CW',
    'version': '12.0.1.0.0',
    'summary': 'RUN-407',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-407
    ''',
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'tis_catch_weight',
    ],
    'data': [
        'views/stock_move_line.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
