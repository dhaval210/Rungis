from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    stock_attribute_line_ids = fields.One2many(
        'stock.lot.attribute.lines',
        'attribute_id',
        'Stock Attribute Lines'
    )
