{
    'name': 'Partner Ranking',
    'summary': 'RUN-1267,RUN-1284',
    'description': """
        RUN-1267:https://jira.metrosystems.net/browse/RUN-1267,
        RUN-1284:https://jira.metrosystems.net/browse/RUN-1284,
        """,
    'version': '12.0.1.0.3',
    'author': 'Cybrosys for METRONOM GmbH',
    'category': 'Enhancement',
    'depends': [
        'base', 'metro_rungis_dashboard'
    ],
    'data': [
        'views/res_partner.xml',
        'data/partner_data.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'Other proprietary',
    'installable': True,
}
