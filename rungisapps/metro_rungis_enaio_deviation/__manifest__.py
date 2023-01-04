{
    'name': "metro_rungis_enaio_deviation",
    'summary': """
        RUN-967
    """,
    'description': """
        https://jira.metrosystems.net/browse/RUN-967,
        V0.2 --> Bug Fixes
    """,
    'author': "Ankita Padhi",
    'category': 'Uncategorized',
    'version': '12.0.1.0.2',
    'depends': [
        'metro_softm_fields',
    ],
    'data': [
        'data/enaio_company_parameter.xml',
        'security/ir.model.access.csv',
        'views/enaio_deviation_remark_view.xml',
        'views/enaio_delivery_deviation.xml'
    ],
    'image': '',
    'license': 'AGPL-3',
}
