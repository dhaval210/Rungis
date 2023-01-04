{
    'name': "Metro Custom Layout",
    'version': '12.0.1.0.4',
    'summary': "RUN-349",
    'description': "RUN-349 :https://jira.metrosystems.net/browse/RUN-349",
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': ['base','purchase'],
    'data': [
        'views/res_company_view.xml',
        'views/report_templates.xml',
        'views/layout_template.xml',
        'report/purchase_order_templates.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
}
