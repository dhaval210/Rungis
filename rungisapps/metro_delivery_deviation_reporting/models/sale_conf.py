# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, fields, api
import pytz


class ResPartnerConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    delivery_hour = fields.Float(string='Maximum Allowed Delivery Time:',
                                 track_visibility='onchange')
    timezone = fields.Selection(
        "_get_timezones",
        string="Timezone",
        default="UTC")

    @api.onchange('delivery_hour')
    def _onchange_hours(self):
        # avoid negative or after midnight
        self.delivery_hour = min(self.delivery_hour, 24.00)
        self.delivery_hour = max(self.delivery_hour, 0.0)

    @api.model
    def _get_timezones(self):
        return [(x,x) for x in pytz.all_timezones]

    @api.model
    def get_values(self):
        res = super(ResPartnerConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            delivery_hour=get_param(
                'metro_delivery_deviation_reporting.delivery_hour'),
        )
        res.update(
            timezone=get_param(
                "metro_delivery_deviation_reporting.timezone"
            )
        )
        return res

    @api.multi
    def set_values(self):
        super(ResPartnerConfiguration, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("metro_delivery_deviation_reporting.delivery_hour",
                          self.delivery_hour)
        ICPSudo.set_param("metro_delivery_deviation_reporting.timezone",
            self.timezone)