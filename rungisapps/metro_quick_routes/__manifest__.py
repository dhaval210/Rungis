{
    'name': 'Metro Quick Routes',
    'version': '12.0.1.0.1',
    'summary': """"Module to quickly generate routes, Run-1023 - https://jira.metrosystems.net/browse/RUN-1023""",
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_quick_routes.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
