{
    'name': 'Stock Evaluation Report',
    'version': '12.0.1.0.14',
    'summary': 'This module allow you to print financial stock report, RUN-825, RUN-1128, RUN-1102, RUN-1163, RUN-1304 ',
    'description': """'RUN-825:https://jira.metrosystems.net/browse/RUN-825',
                      'RUN-1128:https://jira.metrosystems.net/browse/RUN-1128'
                      'RUN-1102:https://jira.metrosystems.net/browse/RUN-1102'
                      'RUN-1163:https://jira.metrosystems.net/browse/RUN-1163'
                      'RUN-1304:https://jira.metrosystems.net/browse/RUN-1304'
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Inventory',
    'depends': [
        'stock', 'purchase', 'metro_stock_landed_cost_vendor'
    ],
    'data': [
        'views/report_menu_view.xml',
        'views/templates.xml',
        'views/product.xml',
        'wizards/wizard.xml',
        'reports/report.xml',
        'reports/report_pdf_template.xml',
        'data/update_lpp_cron.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    # "post_init_hook": "set_last_purchase_price",

}
