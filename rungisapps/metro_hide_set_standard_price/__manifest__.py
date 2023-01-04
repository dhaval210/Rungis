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
    'name': "Hide 'Update Cost' on the product form",
    'version': '0.1',
    'category': 'Metro',
    'description': """
---This is a Proof of Concept---
Hides the button "Update Cost" on the product template and variant, the button is only visible in developer mode.
    """,
    'author': 'Odoo SA',
    'depends': [
        'stock_account',
    ],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
