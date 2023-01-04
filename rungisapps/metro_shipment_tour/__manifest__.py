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
    'name': 'Shipment to tour assignment',
    'summary': 'EMO-225,EMO-456,EMO-581',
    'description': """
EMO-225: Shipment to tour assignment (TMS integration) - Adds truck_id on the SO, to set it as related field on the pickings linked to the SO. Add the field in the picking tree, form and search views.
EMO-456: Add the field in the payment form, tree and search views.
EMO-581: Add the Customer Delivery Date on the Picking coming from the Requested Date on the linked SO, else its Commitment Date. Add group by day in search view.
        """,
    'author': 'Odoo SA',
    'version': '0.3',
    'category': 'Metro',
    'depends': [
        'stock',
        'sale',
        'sale_stock',
        'account',
    ],
    'data': [
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
}
