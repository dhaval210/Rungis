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
    'name': 'Full location name on pickings',
    'summary': 'EMO-264',
    'description': """
EMO-264 Internal Locations in Odoo showing only short names but no nested name of parent location, add package in the same treeview.
        """,
    'author': 'Odoo SA',
    'version': '0.2',
    'depends': [
        'stock',
        'delivery',
    ],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
}
