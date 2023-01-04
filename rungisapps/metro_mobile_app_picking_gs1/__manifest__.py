{
    'name': 'GS1 HHT Enhancement',
    'version': '12.0.1.0.4',
    'summary': 'RUN-209, RUN-1074',
    'description': '''
        RUN-209: https://jira.metrosystems.net/browse/RUN-209,
        RUN-1074: https://jira.metrosystems.net/browse/RUN-1074
    ''',
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
        "Niklas Hucke",
    ],
    'depends': [
        'base_gs1_barcode',
        'metro_app_picking_enhancement',
    ],
    'external_dependencies': {
        'python': [
            'dateparser',
        ],
    },      
    'installable': True,
    'auto_install': False,
    'application': False,
}
