from odoo import api, fields, models


class ouput(models.Model):
    _name = 'tspbv.output'
    _description = 'ouput'

    lydia_output = fields.Char(string='Output Message')
    lydia_copilot = fields.Char(string='Copilot Message')
    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.lydia_output

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res

