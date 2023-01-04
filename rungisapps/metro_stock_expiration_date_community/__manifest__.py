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
    'name': 'Set expiration date on lot creation',
    'summary': 'EMO-263,EMO-695,EMO-717,EMO-718,EMO-779,RUN-104',
    'description': """
EMO-263: Enter the Expiration Date of the product during LOT creation at receiving.
EMO-695: Best Before Date automatically appeared after selecting Lot No.
EMO-717: lots without expiry date
EMO-718: Auto calculation after changing Dates in Lot Number.
EMO-779: Shelf Life alert at time of receiving.
v12 migration: putaway strategy is applied when creating a new stock move line.
        """,
    'author': 'Odoo SA,''Cybrosys for METRONOM GmbH',
    'version': '1.8',
    'depends': [
        'sync_quality_control',
        'stock',
        'product_expiry',
        'metro_alert_expiration_community'
    ],
    'data': [
        'views/product_views.xml',
        'views/stock_views.xml',
    ],
    'installable': True,
}
