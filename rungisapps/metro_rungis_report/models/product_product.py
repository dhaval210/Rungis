# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    total_cost = fields.Float(string="Current Cost",
                              compute="_compute_inventory_turn_report",
                              help="= Qty. on hand x Current Cost")

    def _compute_inventory_turn_report(self):
        res = super(ProductProduct, self)._compute_inventory_turn_report()
        for prod in self:
            if prod.catch_weight_ok:
                prod.total_cost = prod.cw_qty_available * prod.standard_price
        return res
