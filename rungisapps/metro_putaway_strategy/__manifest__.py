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
    'name': 'Custom putaway strategy',
    'summary': 'EMO-377,EMO-908',
    'description': """
EMO-377: Metro Putaway Strategy Custom Module. EMO-908: proposes empty location also for packs.
        """,
    'author': 'Odoo SA',
    'category': 'Metro',
    'version': '0.5',
    'depends': ['stock'],
    'data': [
        'views/product_strategy.xml',
        'views/location.xml',
        'views/product.xml',
        ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
