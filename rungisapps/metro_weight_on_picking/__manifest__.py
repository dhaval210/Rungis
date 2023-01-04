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
    'name': 'Weight fields on the Picking Treeview',
    'summary': 'EMO-256',
    'category': 'Metro',
    'description': """
EMO-256: add "weight" and "shipping weight" fields to the pick order views,
Refactoring from Odoo Studio
        """,
    'author': 'Odoo SA',
    'version': '0.1',
    'depends': [
        'stock',
        'delivery',
    ],
    'data': [
        'data/ir_ui_view.xml',
    ],
    'installable': True,
}
