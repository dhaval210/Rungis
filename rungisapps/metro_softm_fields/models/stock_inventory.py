from odoo import fields, models


class InventoryAdjustment(models.Model):
    _inherit = 'stock.inventory'

    send_to_softm = fields.Boolean(
        string="SoftM Status",
        default=False,
    )
