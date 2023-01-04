# -*- coding: utf-8 -*-

{
    'name': 'Stock Landed cost Vendor Percentage',
    'summary': 'This module allow you to apply fixed percentage of landed costs to every received items based on vendor , RUN-825',
    'description': 'RUN-825:https://jira.metrosystems.net/browse/RUN-825',
    'version': '12.0.1.0.1',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'category': 'Purchase',
    'depends': ['stock_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

