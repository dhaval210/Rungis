# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    margin = fields.Float(compute='_compute_margin', string="Margin(%)", readonly=True)

    @api.depends('product_variant_ids', 'product_variant_ids.default_code', 'lst_price', 'standard_price')
    def _compute_margin(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.margin = template.product_variant_ids.margin
        for template in (self - unique_variants):
            template.margin = 0

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if self.list_price - self.standard_price < 0:
            raise UserError(_("The margin is negative!"))


class ProductProduct(models.Model):
    _inherit = "product.product"

    margin = fields.Float(compute='_compute_margin', string="Margin(%)", readonly=True)

    @api.depends('list_price','standard_price')
    def _compute_margin(self):
        for prod in self:
            if prod.list_price and prod.standard_price:
                prod.margin = (prod.list_price - prod.standard_price)*100/prod.list_price
            else:
                prod.margin = 0

    @api.onchange('lst_price')
    def _onchange_lst_price(self):
        if self.lst_price - self.standard_price < 0:
            raise UserError(_("The margin is negative!"))
