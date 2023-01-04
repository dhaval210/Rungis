# -*- encoding: utf-8 -*-

{
    'name': 'Metro Article Calculation',
    'version': '12.0.1.0.10',
    'summary': 'RUN-296, RUN-580, RUN-935',
    'description': """RUN-296:https://jira.metrosystems.net/browse/RUN-296,
                      RUN-935:https://jira.metrosystems.net/browse/RUN-935""",
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'product',
        'purchase_triple_discount',
        'stock_landed_costs',
        'average_landed_cost',
        'tis_catch_weight'

    ],
    'data': [
        'views/product_supplierinfo_view.xml',
        'views/product_template_view.xml',
        'report/product_template_templates.xml',
        'report/product_reports.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
}

