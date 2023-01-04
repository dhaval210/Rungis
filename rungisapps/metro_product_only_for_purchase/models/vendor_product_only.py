# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    vendor_product = fields.Boolean(default=True,
                                    string="Vendor's Product Only")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_id_filter = fields.Many2one('product.product', string='Product')

    @api.onchange('product_id_filter')
    def _onchange_product(self):
        self.product_id = self.product_id_filter.id
