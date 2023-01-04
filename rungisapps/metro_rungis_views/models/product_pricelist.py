from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[('last_purchase_price', 'LPP')])