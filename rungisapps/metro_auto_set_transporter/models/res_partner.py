from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    transporter_id = fields.Many2one('res.partner')
