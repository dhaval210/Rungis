# -*- coding: utf-8 -*-
from odoo import models, fields, api
import pytz

class PurchaseConfiguration(models.TransientModel):
    _inherit = "res.config.settings"

    tolerance = fields.Float(string="Tolerance in hours")
    timezone = fields.Selection(
        "_get_timezones",
        string="Timezone",
        default="UTC"
    )

    @api.model
    def _get_timezones(self):
        return [(x,x) for x in pytz.all_timezones]

    @api.model
    def get_values(self):
        res = super(PurchaseConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            tolerance=get_param(
                'metro_po_delivery_deviation_reporting.tolerance'),
        )
        return res

    @api.multi
    def set_values(self):
        super(PurchaseConfiguration, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("metro_po_delivery_deviation_reporting.tolerance",
                          self.tolerance)
        ICPSudo.set_param("metro_po_delivery_deviation_reporting.timezone",
                          self.timezone)
