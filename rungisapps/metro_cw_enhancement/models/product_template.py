from odoo.addons import decimal_precision as dp
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    @api.depends('product_variant_ids', 'product_variant_ids.average_cw_quantity')
    def _compute_avg_qty(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.average_cw_quantity = template.product_variant_ids.average_cw_quantity
        for template in (self - unique_variants):
            template.average_cw_quantity = 0.0

