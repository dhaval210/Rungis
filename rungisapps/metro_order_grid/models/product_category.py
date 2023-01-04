from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    ultra_fresh_threshold = fields.Integer(
        help="this field sets the default lifetime per category for products without bbd",
        default=5
    )
