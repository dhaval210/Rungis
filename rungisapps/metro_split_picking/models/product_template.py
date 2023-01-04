from odoo import _, api, fields, models, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    transport_id = fields.Many2one('transport.unit', 'Transport')
    base_qty = fields.Float('Base Pickeable Quantity')
