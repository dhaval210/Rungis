from odoo import api, fields, models


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    softm_key = fields.Char()
