from odoo import api, fields, models


class Product(models.Model):
    _inherit = 'product.template'

    collect_data = fields.Boolean(string='Collect data')
