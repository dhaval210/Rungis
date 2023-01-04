{
    'name': 'Metro Async Order Confirm',
    'version': '12.0.1.0.11',
    'summary': 'RUN-657,RUN-1007,RUN-1097,RUN-774,RUN-1116,RUN-1122,RUN-1278,RUN-1049',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-657
        https://jira.metrosystems.net/browse/RUN-1007
        https://jira.metrosystems.net/browse/RUN-1097
        https://jira.metrosystems.net/browse/RUN-774
        https://jira.metrosystems.net/browse/RUN-1116
        https://jira.metrosystems.net/browse/RUN-1122
        https://jira.metrosystems.net/browse/RUN-1278
        https://jira.metrosystems.net/browse/RUN-1049
    ''',
    'category': 'Enhancement',
    'author': '''
        Thore Baden, Huckemedia GmbH & Co. KG
    ''',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'purchase',
        'metro_validate_pack',
        'queue_job',
        'metro_procurement_manager',
    ],
    'data': [
        'views/purchase_order.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
