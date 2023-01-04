{
    'name': "Metro Mhd Barcode Community",
    'version': '12.0.1.1.3',
    'summary': "RUN-476,RUN-407,RUN-667,RUN-741",
    'description': """
        RUN-476 :https://jira.metrosystems.net/browse/RUN-476
        RUN-407 :https://jira.metrosystems.net/browse/RUN-407
        RUN-741: https://jira.metrosystems.net/browse/RUN-741
    """,
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'stock',
        'metro_stock_expiration_date_community',
    ],
    'data': [
        'views/stock_move_line.xml',
        'views/stock_picking.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
}
