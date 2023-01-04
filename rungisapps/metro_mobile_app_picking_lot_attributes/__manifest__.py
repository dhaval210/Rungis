{
    'name': 'Bugfix for Dest Pack in Move Line',
    'version': '12.0.1.1.0',
    'summary': 'RUN-637,RUN-646',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-637,
        https://jira.metrosystems.net/browse/RUN-646,
    ''',
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'metro_app_picking_enhancement',
        'metro_lot_attributes',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
