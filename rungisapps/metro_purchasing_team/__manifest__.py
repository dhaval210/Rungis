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
    'name': 'Purchasing Team on Products',
    'summary': 'EMO-639',
    'description': """
In the Product Categories form, a new field “Purchasing Team” shall be added immediately under Category Type, maintainable through a predefined List of Values. 
Maintenance of the possible values for Main Category shall be done in the Configuration menu of the Purchases app; initial values shall be:
- HoReCa
- NonFood
- Traders
- UltraFresh & Frozen 
The new field shall be available for custom filtering and for custom grouping in the Products and Product Variants forms.
        """,
    'author': 'Odoo SA',
    'version': '0.1',
    'module': 'Metro',
    'depends': [
        'product',
        'purchase',
    ],
    'data': [
        'views/product_views.xml',
        'security/ir.model.access.csv',
        'data/purchasing_team_data.xml',
    ],
    'installable': True,
}
