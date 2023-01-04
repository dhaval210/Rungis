# -*- coding: utf-8 -*-

##############################################################################
#
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
    'name': "Adding Best Before Date and Alert Date under Quants",

    'summary': """
        EMO-1093
        """,

    'description': """
        EMO-1093 Adding Best Before Date and Alert Date under Quants.
    """,

    'author': "Metro Wholesale Myanmar",
    'website': "http://www.metro-wholesale.com.mm",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product_expiry'],

    # always loaded
    'data': [              
        'views/view_quant_extend.xml',
    ],
   
}