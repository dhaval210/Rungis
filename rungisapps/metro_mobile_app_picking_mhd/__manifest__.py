{
    'name': 'MHD Barcode Enhancement',
    'version': '12.0.1.2.8',
    'summary': 'RUN-725,RUN-741,RUN-973',
    'description': """
        RUN-725 :https://jira.metrosystems.net/browse/RUN-725
        RUN-741: https://jira.metrosystems.net/browse/RUN-741
        RUN-973: htpps://jira.metrosystems.net/browse/RUN-973
    """,
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
        'Niklas Tom Hucke'
    ],
    'depends': [
        'metro_app_picking_enhancement',
    ],
    'external_dependencies': {
        'python': [
            'dateparser',
        ],
    },    
    'data': [
        # 'views/stock_move_line.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
