# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Customer Family',
    'summary': 'EMO-561',
    'description': """
EMO-561: Enhance the dynamic reporting by the customer family
        """,
    'author': 'Odoo SA',
    'version': '0.1',
    'module': 'Metro',
    'depends': [
        'base',
        'sale',
        'sales_team',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/partner_family_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
