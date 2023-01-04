{
    'name': 'Metro Rungis Access',
    'version': '12.0.1.0.1',
    'summary': 'RUN-864,RUN-964',
    'description': """
                RUN-864:https://jira.metrosystems.net/browse/RUN-864,
                RUN-964:https://jira.metrosystems.net/browse/RUN-964,
                """,
    'author': 'Cybrosys for METRONOM GmbH',
    'category': 'Enhancement',
    'depends': ['base','purchase','stock','sale','mrp'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_warehouse_orderpoint.xml'],
    'license': 'Other proprietary',
    'installable': True,
}