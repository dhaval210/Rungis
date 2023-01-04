{
    'name': 'metro_gate_management',
    'summary': 'RUN-75,RUN-321,RUN-690,RUN-1270',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-75
        https://jira.metrosystems.net/browse/RUN-321
        https://jira.metrosystems.net/browse/RUN-690
        https://jira.metrosystems.net/browse/RUN-1270
    ''',
    'author': 'Hucke Media GmbH & Co. KG,Cybrosys for METRONOM GmbH',
    'website': 'https://www.hucke-media.de',
    'category': 'Uncategorized',
    'version': '12.0.1.1.9',
    'depends': [
        'stock',
        'stock_picking_batch',
        'odoo_transport_management',
    ],
    'data': [
        'data/res_config_settings_data.xml',
        'data/stock_gate_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/stock_gate_views.xml',
        'views/stock_picking_views.xml',
        'views/resources.xml'
    ],
    'demo': [
        'demo/stock_gates_demo.xml'
    ],
    'license': 'AGPL-3',
}
