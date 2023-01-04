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
    'name': 'Mandatory Analytic Accounts in Vendor Bill',
    'summary': 'EMO-395',
    'description': """
EMO-395: Analytic Accounts in Vendor Bills have to be mandatory (no default value)   
        """,
    'author': 'Odoo SA',
    'version': '0.1',
    'category': 'Metro',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice_views.xml',
    ],
    'installable': True,
}
