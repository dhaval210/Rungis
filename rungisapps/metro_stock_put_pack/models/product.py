# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    apply_packrules = fields.Boolean('Apply Pack Rules')
    allow_variants = fields.Boolean('Only Allow Variants', help="Only Allow variants of this template to be put in the same pack")
    allow_same_category = fields.Boolean('Only Allow Same Category', help="Only Allow products of the same category to be put in the same pack")
    stock_product_rule_ids = fields.One2many('stock.pack.product.rule', 'product_id', string="Stock Pack Product Rule", help="Only allow packs with products sharing the same characteristics")
