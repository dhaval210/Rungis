# -*- encoding: utf-8 -*-
import ast

from odoo import models, fields


class PurchaseScheduleConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    schedule_duration = fields.Selection([
        ('5', '5 minutes'),
        ('10', '10 minutes'),
        ('15', '15 minutes'),
        ('30', '30 minutes'),

    ], 'Default Duration', required=True, index=True, default='5')
    tags = fields.Many2many('calendar.event.type', string='Tags')
    number_of_weeks = fields.Integer("Number of Weeks")

    def set_values(self):
        """ save values in the settings fields """

        super(PurchaseScheduleConfigSettings, self).set_values()
        tags = self.tags.ids if self.tags else False
        self.env['ir.config_parameter'].sudo().set_param('purchase_schedule.schedule_duration', self.schedule_duration)
        self.env['ir.config_parameter'].sudo().set_param('purchase_schedule.tags', tags)
        self.env['ir.config_parameter'].sudo().set_param('purchase_schedule.number_of_weeks', self.number_of_weeks)

    def get_values(self):
        """
        Get the saved values for fields
        """
        res = super(PurchaseScheduleConfigSettings, self).get_values()
        duration = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.schedule_duration', default=False)
        tags = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.tags', default=False)
        number_of_weeks = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.number_of_weeks', default=False)
        res.update(
            schedule_duration=duration,
            tags=[(6, 0, ast.literal_eval(str(tags)))],
            number_of_weeks=int(number_of_weeks)
        )
        return res
