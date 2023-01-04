from odoo import _, api, fields, models, tools


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    transport_id = fields.Many2one('transport.unit', 'Transport')
