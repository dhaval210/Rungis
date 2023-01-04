# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_quality_control_allow = fields.Boolean("Allow to modify Control Point.",
                                                  help="If we select this boolean then system will allow to edit "
                                                       "Control point if not related inspection line is created.")
    always_detailed_quality_inspection = fields.Boolean('Always Detailed Quality Inspection', config_parameter='sync_quality_control.always_detailed_quality_inspection', default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['module_quality_control_allow'] = self.env['ir.config_parameter'].sudo().get_param(
            'sync_quality_control.module_quality_control_allow')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('sync_quality_control.module_quality_control_allow',
                                                         self.module_quality_control_allow)
        super(ResConfigSettings, self).set_values()
