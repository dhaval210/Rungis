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
    'summary': 'RUN-1244,1242',
    'description': """
        https://jira.metrosystems.net/browse/RUN-1242,
        https://jira.metrosystems.net/browse/RUN-1244,
        fix field dependency error
        """,
    'author': 'Odoo SA',
    'version': '12.0.0.10',
    'module': 'Metro',
    'depends': [
        'product',
        'sale_margin',
        'account',
        'metro_rungis_inventory_value_report',
        'sale_global_discount'
    ],
    'data': [
        'views/sale_order_views.xml',
        #'views/invoice_views.xml',
        #'views/purchase_order_view.xml' ##CAn be uncommented when reqd. by the business.
    ],
    'installable': True,
}
