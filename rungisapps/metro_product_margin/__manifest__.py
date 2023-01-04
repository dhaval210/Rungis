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
    'name': 'Margin on Product',
    'summary': 'EMO-480,EMO-563,EMO-641,EMO-792',
    'description': """
EMO-480: Product form: as a category manager, I need to see the product calculated margin, because it is business critical information.
EMO-563: Margin reporting in Percent.
EMO-641: Include additional buying costs in margin calculation. v0.5: on the SO, v0.6: on the SO and the invoice, v0.7: field labels and display all fields only in SO/Invoice line pop-up.
        """,
    'author': 'Odoo SA',
    'version': '0.7',
    'module': 'Metro',
    'depends': [
        'product',
        'sale_margin',
        'metro_landed_costs',
        'account',
    ],
    'data': [
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/invoice_views.xml',
    ],
    'installable': True,
}
