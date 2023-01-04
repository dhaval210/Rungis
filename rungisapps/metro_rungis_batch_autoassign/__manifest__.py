{
    'name': 'Rungis autoassign Picking to Batch',
    'version': '12.0.1.2.6',
    'summary': 'RUN-507,RUN-652,RUN-752,RUN-822,RUN-972,RUN-1007',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-507,
        https://jira.metrosystems.net/browse/RUN-652,
        https://jira.metrosystems.net/browse/RUN-752,
        https://jira.metrosystems.net/browse/RUN-822,
        https://jira.metrosystems.net/browse/RUN-972,
        https://jira.metrosystems.net/browse/RUN-1007,
    ''',
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'metro_min_amount_so',
        'metro_procurement_manager',
        'metro_hub_management',
        'metro_softm_fields',
        'queue_job'
    ],
    'data': [
        'views/stock_picking_type.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
