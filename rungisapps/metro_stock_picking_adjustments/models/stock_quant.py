from odoo import models, fields


class StockQuant(models.Model):
    _inherit = "stock.quant"

    message_channel_ids = fields.Many2many(
        related="lot_id.message_channel_ids",
        string="Subscriber (Channels)",
    )
