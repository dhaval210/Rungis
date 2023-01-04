{
    'name': 'metro_security_roles',
    'summary': 'RUN-290,RUN-1263',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-290
        RUN-1263:https://jira.metrosystems.net/browse/RUN-1263
    ''',
    'author': 'Hucke Media GmbH & Co. KG',
    'website': 'https://www.hucke-media.de',
    'category': 'Uncategorized',
    'version': '12.0.1.0.8',
    'depends': [
        'account',
        'base_user_role',
        'metro_gate_management',
        'odoo_transport_management',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_inventory.xml'
    ],
    'image': '',
    'license': 'AGPL-3',
}
