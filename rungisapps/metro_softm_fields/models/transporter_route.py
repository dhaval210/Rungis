from odoo import fields, models, api, _
from odoo.exceptions import UserError


class TransportRoute(models.Model):
    _inherit = 'transporter.route'

    tour_name = fields.Char(string='tour name')
    tour_group = fields.Char(string='tour group')
    tour_depot = fields.Char(string='tour depot')
    company_id = fields.Many2one('res.company', string='company')
    tour_default_departure = fields.Float(digits=(12, 2), string="Default Departure")

    @api.onchange('tour_default_departure')
    def departure_validations(self):
        time = self.tour_default_departure
        if time >= 24:
            raise UserError(_("The Time is not valid, it needs to be under 24:00"))
