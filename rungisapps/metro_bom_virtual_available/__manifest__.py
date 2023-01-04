# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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
    'name': 'Stock display of make-to-order articles',
    'version': '0.2',
    'summary': 'EMO-829',
    'category': 'Metro',
    'description': """
---This is a Proof of Concept, not suited for big volumetries---
Adds a smart button on BOM-Products "Can be Manufactured", counting how many products could be manufactured taking into account the first available BOM and the availability of those BOM-components.
The Smart Button opens those components in a grouped treeview.  
    """,
    'author': 'Odoo SA',
    'depends': [
        'product',
        'stock',
        'mrp',
    ],
    'data': [
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
