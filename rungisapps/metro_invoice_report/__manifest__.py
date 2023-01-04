# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-TODAY Odoo S.A. <http://www.odoo.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Metro Invoice Report',
    'version': '0.1',
    'summary': 'EMO-792',
    'description': """
    EMO-792: Enhancement of the Accounting>Reports>Invoices report
    """,
    'category': 'Metro',
    'website': 'http://odoo.com',
    'depends': ['account', 'metro_buying_potential', 'metro_landed_costs', 'metro_product_margin'],
    'data': [
        # views
        'views/invoice_view.xml',
        # security
        'security/ir.model.access.csv',
    ],
    'demo': [],

    'installable': True,
    'application': False,
    'auto_install': False,
}
