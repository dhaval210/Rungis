# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Minimum Order Value restriction on Sales Order creation',
    'summary': 'EMO-477,EMO-731,EMO-831',
    'description': """
EMO-477: Restriction on creating SO which is below Standard Minimum order value. Set the values on the company for KAC and non-KAC.
v0.2: Changed from amount_total to amount_untaxed as calculation basis, 
EMO-731 (v0.3): Configurable limit for Employees, set fixed delivery addresses (configured on company) on SO if customer is employee.
EMO-831 (v0.4): KAC checkbox for subcontacts is synced with parent contact.
Migration (v0.5): adds the view on res.partner from nisu modules metro_custom_sales and key_account_customer.
        """,
    'author': 'Odoo SA',
    'version': '0.5',
    'module': 'Metro',
    'depends': [
        'base',
        'sale',
        'sales_team',
        'hr',
    ],
    'data': [
        'views/res_company_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
}
