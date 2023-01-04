from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    sort = fields.Integer(string='Sort')
    check_digit = fields.Integer(string='Check Digit')
    zone = fields.Integer(string='Zone')
    session_ids = fields.One2many(
        comodel_name='tspbv.session',
        inverse_name='current_location_id',
        string='Pick by Voice User'
    )
