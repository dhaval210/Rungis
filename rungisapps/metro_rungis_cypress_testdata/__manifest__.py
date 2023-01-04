{
    'name': 'Rungis Testdata for Cypress',
    'version': '12.0.1.0.1',
    'summary': 'RUN-345',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-345,
        Rungis Testdata for Purchase workflow
    ''',    
    'category': 'Testing',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https//www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'tis_catch_weight', 'metro_gate_management'
    ],
    'data': [
        'data/cw_data.xml',
        'data/non_cw_data.xml',
        'data/cypress_data.xml',
        'data/purchase_data.xml',
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/cypress_data.xml',
        'views/cypress_purchase_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
