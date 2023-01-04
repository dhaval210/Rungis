from odoo import _, api, fields, models, tools


class ProductCategory(models.Model):
    _inherit = 'product.category'

    transport_id = fields.Many2one('transport.unit', 'Transport')
