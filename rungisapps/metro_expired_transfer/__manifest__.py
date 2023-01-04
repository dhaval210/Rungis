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
    'name': 'Automatic draft transfer for expired stock',
    'summary': 'EMO-333, RUN-827, RUN-855',
    'description': """
EMO-333: Prevent expired products from being picked (for customer delivery) in Inventory 
- Creates automatically an internal transfer containing all expired products to the scrap location and internal operation type defined on the warehouse. 
        , RUN-827: https://jira.metrosystems.net/browse/RUN-827,
          RUN-855: https://jira.metrosystems.net/browse/RUN-855""",
    'author': 'Odoo SA, Cybrosys for METRONOM GmbH',
    'version': '0.4',
    'category': 'Metro',
    'depends': [
        'stock',
        'tis_catch_weight'
    ],
    'data': [
        'views/stock_warehouse.xml',
        'data/auto_transfer_data.xml',
    ],
    'installable': True,
}
