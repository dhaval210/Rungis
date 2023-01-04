# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    margin = fields.Float(compute='_compute_margin',  string="Margin(%)", readonly=True)

    @api.depends('list_price', 'last_purchase_price')
    def _compute_margin(self):
        for prod in self:
            if prod.list_price and prod.last_purchase_price:
                prod.margin = (prod.list_price - prod.last_purchase_price)/prod.list_price
            else:
                prod.margin = 0



class ProductProduct(models.Model):
    _inherit = "product.product"

    margin = fields.Float(compute='_compute_margin',  string="Margin(%)", readonly=True)

    @api.depends('list_price','last_purchase_price')
    def _compute_margin(self):
        for prod in self:
            if prod.list_price and prod.last_purchase_price:
                prod.margin = (prod.list_price - prod.last_purchase_price)/prod.list_price
            else:
                prod.margin = 0

