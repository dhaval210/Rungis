# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Buying potential and Sales Target on Partner',
    'summary': 'EMO-562',
    'version': '1.2',
    'category': 'Metro',
    'description': """
Adds the buying potential field on the partner form and tree view, adds a pivot and graph view on res.partner.
EMO-562: adds the sales target field.
    """,
    'author': 'Odoo SA',
    'depends': [
        'contacts',
        'sales_team',
        'account',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
