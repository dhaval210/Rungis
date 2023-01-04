from odoo import api, fields, models


class Scan(models.Model):
    _name = 'tspbv.scan'
    _description = 'Scan'

    rel = fields.Char(string='Relation ID')
    input_id = fields.Many2one(
        comodel_name='tspbv.input',
        string='Dialog'
    )
    on_match = fields.Char(string='onMatch')
    pattern = fields.Char(string='Recognition Pattern')

    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.rel

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res
