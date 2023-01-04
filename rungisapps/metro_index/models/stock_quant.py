from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_id = fields.Many2one(
        'stock.production.lot',
        'Lot/Serial Number',
        ondelete='restrict',
        readonly=True,
        index=True
    )
