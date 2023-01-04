{
    'name': 'Metro Validate Pack',
    'version': '12.0.1.1.3',
    'summary': 'RUN-309,RUN-693,RUN-1055,RUN-1049',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-309,
        https://jira.metrosystems.net/browse/RUN-693,
        https://jira.metrosystems.net/browse/RUN-1055,
        https://jira.metrosystems.net/browse/RUN-1049
    ''',
    'category': 'Enhancement',
    'author': '''
        Thore Baden, Huckemedia GmbH & Co. KG
    ''',
    'website': 'https://www.hucke-media.de/',
    'license': 'LGPL-3',
    'depends': [
        'queue_job',
        'stock',
    ],
    'data': [
        'views/stock_picking_type.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
