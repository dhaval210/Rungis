from odoo import _, api, fields, models, tools


class StockLocation(models.Model):
    _inherit = 'stock.location'

    transport_id = fields.Many2one('transport.unit', 'Transport')
