# -*- encoding: utf-8 -*-

{
    'name': 'Metro Sale And Purchase Menu',
    'version': '12.0.1.0.2',
    'summary': 'RUN-367, RUN-405',
    'description': """RUN-367:https://jira.metrosystems.net/browse/RUN-367""",
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'sale',
        'purchase',
        'metro_purchase_schedule'
    ],
    'data': [
        'views/sale_order_line_views.xml',
        'views/purchase_menu_view.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
}
