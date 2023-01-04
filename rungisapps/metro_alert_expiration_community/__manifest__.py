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
    'name': 'Expiration Quality Control',
    'version': '1.10',
    'summary': 'EMO-378' 'EMO-1180' 'RUN-104',
    'category': 'Metro',
    'description': """
Whenever a certain quality control point is built trigger quality alert when expiration date of product compared to use time is smaller than rate on control point.
     EMO-1180:issue related quality alert Fixed (updated 16 Aug 2019)""",
    'author': 'Odoo SA,''Cybrosys for METRONOM GmbH',
    'depends': [
        'sync_quality_control',
        'stock',
    ],
    'data': [
        'views/quality.xml',
        'data/quality_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}