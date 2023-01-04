{
    'name': 'Quality Inspection Extend',
    'version': '12.0.1.0.1',
    'summary': 'RUN-633',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-633
    ''',
    'category': 'Quality',
    'author': 'Huckemedia GmbH & Co KG.',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'sync_quality_control',
    ],
    'data': [
        'views/quality_inspection_line.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
