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
    'name': 'Calculate automatically currency amount on journal items',
    'summary': 'EMO-396',
    'description': """
EMO-396: For foreign currency Journal Entries enter Debit or Credit and derive the Amount currency value from that according to current currency rate, at the moment where currency field is set.
If no debit/credit, then debit/credit will be filled with the converted amount given in the Amount Currency with the specified currency (debit if positive, credit if neagtive).
If the checkbox 'Disable automatic currency calculation' is set, the onchange is not triggered. 
        """,
    'author': 'Odoo SA',
    'version': '0.6',
    'category': 'Metro',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move.xml',
    ],
    'installable': True,
}
