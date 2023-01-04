# -*- coding: utf-8 -*-

{
    'name': 'Manufacturing Automatic Funcationality',
    'summary': 'This module allow you to automate manufacturing functionality , RUN-941, RUN-1076, RUN-1323',
    'description': 'RUN-941:https://jira.metrosystems.net/browse/RUN-941'
                   'RUN-1076:https://jira.metrosystems.net/browse/RUN-1076'
                   'RUN-1323:https://jira.metrosystems.net/browse/RUN-1323',
    'version': '12.0.1.0.7',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'depends': ['mrp', 'metro_mrp_auto_lot'],
    'data': [
        'data/mail_template.xml',
        'views/mrp_production.xml',
        'views/stock_warehouse.xml',
        'data/aproduct_action.xml',
        'views/assets.xml',
    ],
    'qweb': ['static/src/xml/aproduct_not_done.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

