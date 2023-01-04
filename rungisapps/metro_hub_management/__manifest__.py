{
    'name': 'Metro Hub Management',
    'version': '12.0.1.0.6',
    'summary': 'RUN-752,RUN-818,RUN-903',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-752
        https://jira.metrosystems.net/browse/RUN-818
    ''',
    'category': 'Warehouse Management',
    'author': 'Thore Baden, Hucke Media Gmbh & Co. KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'odoo_transport_management',
    ],
    'data': [
        'data/hub_schedule_cron.xml',
        'security/ir.model.access.csv',
        'views/resources.xml',
        'views/stock_picking_batch.xml',
        'views/transporter_hub.xml',
        'views/transporter_route.xml',
        'wizard/transporter_hub_report.xml',
        'views/menu_items.xml',
    ],
    "qweb": [
        'static/src/xml/qweb.xml',
    ],    
    'installable': True,
    'application': True,
    'auto_install': False,
}

