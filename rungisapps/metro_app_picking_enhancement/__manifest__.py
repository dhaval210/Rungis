{
    'name': 'metro_app_picking_enhancement',
    'version': '12.0.1.6.3',
    'summary': 'extending metro_mobile_app_picking; RUN-668, RUN-503, RUN-475,RUN-712,RUN-755,RUN-798,RUN-766,RUN-1051,RUN-683,RUN-1074, RUN-1052, RUN-1283',
    'description': '''
    RUN-668: https://jira.metrosystems.net/browse/RUN-668
    RUN-503: https://jira.metrosystems.net/browse/RUN-503
    RUN-475: https://jira.metrosystems.net/browse/RUN-475
    RUN-798: https://jira.metrosystems.net/browse/RUN-798
    RUN-712: https://jira.metrosystems.net/browse/RUN-712
    RUN-755: https://jira.metrosystems.net/browse/RUN-755
    RUN-766: https://jira.metrosystems.net/browse/RUN-766
    RUN-1051: https://jira.metrosystems.net/browse/RUN-1051
    RUN-683: https://jira.metrosystems.net/browse/RUN-683
    RUN-1074: https://jira.metrosystems.net/browse/RUN-1074
    RUN-1052: https://jira.metrosystems.net/browse/RUN-1052
    RUN-1052: https://jira.metrosystems.net/browse/RUN-1283
    ''',
    'category': 'Stock',
    'author': 'Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'metro_mobile_app_picking',
    ],
    'data': [
        'views/view_stock_picking_type.xml',
        'views/view_picking_type_form_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
