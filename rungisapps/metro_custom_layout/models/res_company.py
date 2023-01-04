"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from datetime import datetime, timedelta
from odoo import models, api, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    top_logo_header = fields.Binary('Top Logo In Header')
    mother_company_logo = fields.Binary('Mother Company Logo')
    back_address = fields.Text('Back Address')
    field_1 = fields.Text('1st Field')
    field_2 = fields.Text('2nd Field')
    field_3 = fields.Text('3rd Field')
    field_4 = fields.Text('4th Field')
    field_5 = fields.Text('5th Field')
    field_6 = fields.Text('6th Field')
    field_7 = fields.Text('7th Field')
    field_8 = fields.Text('8th Field')
    field_9 = fields.Text('9th Field')
    field_10 = fields.Text('10th Field')
    field_11 = fields.Text('11th Field')
    field_12 = fields.Text('12th Field')
    field_13 = fields.Text('13th Field')
    field_14 = fields.Text('14th Field')
    field_15 = fields.Text('15th Field')
    field_16 = fields.Text('16th Field')
    field_17 = fields.Text('17th Field')
