{
    'name': "Metro Update Zero Cost for Stock Move",
    'version': '12.0.0.0.2',
    'summary': "RUN-1047",
    'description': """
        RUN-1047 :https://jira.metrosystems.net/browse/RUN-1047,
    """,
    'author': ' Ankita Padhi',
    'category': 'Metro',
    'depends': ['tis_catch_weight','metro_security_roles','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_edit_view.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
}
