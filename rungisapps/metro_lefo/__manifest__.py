{
    'name': "Metro Lefo Management",
    'version': '12.0.1.0.4',
    'summary': "RUN-268, RUN-772",
    'description': """
        RUN-268 :https://jira.metrosystems.net/browse/RUN-268,
        RUN-772 :https://jira.metrosystems.net/browse/RUN-772,
    """,
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': ['stock','metro_putaway_strategy','tis_catch_weight'],
    'data': [
        'data/product_removal.xml',
        'views/res_partner_view.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
}
