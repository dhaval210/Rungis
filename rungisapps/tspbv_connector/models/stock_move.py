from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    session_id = fields.Many2one(
        comodel_name='tspbv.session',
        string='PbV Session ID'
    )
    voice_picked = fields.Boolean(string='picked by voice')
