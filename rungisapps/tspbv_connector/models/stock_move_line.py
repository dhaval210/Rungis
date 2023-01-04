from odoo import api, fields, models


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    session_id = fields.Many2one(
        comodel_name='tspbv.session',
        string='PbV Session ID'
    )
    voice_picked = fields.Boolean(string='picked by voice')
    sort = fields.Integer(string='Sort Order', default=1)
