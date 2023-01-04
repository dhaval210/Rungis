{
    'name': 'Fish Label report',
    'version': '12.0.1.0.9',
    'summary': 'This module helps to print fish product label,RUN-883,RUN-1111,RUN-1014',
    'description': """
                   RUN-883 : https://jira.metrosystems.net/browse/RUN-883 
                   RUN-1111 : https://jira.metrosystems.net/browse/RUN-1111
                   RUN-1014 : https://jira.metrosystems.net/browse/RUN-1014
    """,
    'category': 'Enhancement',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'depends': ['product', 'base','stock', 'metro_barcode_print_community'],
    'data': [
        'data/fish_product_categ.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/stock_picking.xml',
        'report/fishlabelreport_template.xml',
        'report/report.xml',
        'wizard/fish_label_report_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
