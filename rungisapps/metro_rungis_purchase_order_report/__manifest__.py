{
    'name': 'Metro Rungis Purchase Order Report',
    'version': '12.0.1.0.36',
    'summary': 'RUN-224, RUN-711,RUN-764, RUN-674, RUN-896, RUN-986, RUN-1033, RUN-1030, RUN-1060, RUN-1119,RUN-1087',
    'description': """
                RUN-224 :https://jira.metrosystems.net/browse/RUN-224
                RUN-711 :https://jira.metrosystems.net/browse/RUN-711
                RUN-764 :https://jira.metrosystems.net/browse/RUN-764
                RUN-674 :https://jira.metrosystems.net/browse/RUN-674
                RUN-896 :https://jira.metrosystems.net/browse/RUN-896
                RUN-896 :https://jira.metrosystems.net/browse/RUN-986
                RUN-1036 :https://jira.metrosystems.net/browse/RUN-1036
                RUN-1033 :https://jira.metrosystems.net/browse/RUN-1033
                RUN-1030 :https://jira.metrosystems.net/browse/RUN-1030
                RUN-1060 :https://jira.metrosystems.net/browse/RUN-1060
                RUN-1119 :https://jira.metrosystems.net/browse/RUN-1119
                RUN-1087 :https://jira.metrosystems.net/browse/RUN-1087


               """,
    'category': 'Metro',
    'author': 'Cybrosys for METRONOM GmbH',
    'depends': [
        'purchase',
        'tis_catch_weight',
        'purchase_discount',
        'metro_softm_fields',
        'metro_rungis_delivery_date_control',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/purchase_order_templates.xml',
        'reports/purchase_quotation_templates.xml',
        'views/purchase_order_line.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
    'auto_install': False,
    'application': False,
}
