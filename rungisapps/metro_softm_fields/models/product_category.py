from odoo import models, fields


class MetroExtend_ProductCategory(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one('res.company', string='company')
    external_product_category = fields.Char()
