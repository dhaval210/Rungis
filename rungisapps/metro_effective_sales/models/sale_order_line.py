# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    effective_sales = fields.Monetary(compute='_compute_effective_sales', string='Effective Sales',
                                      currency_field='currency_id', readonly=True, store=True)

    @api.depends('qty_delivered', 'discount', 'price_unit')
    def _compute_effective_sales(self):
        for line in self:
            line.effective_sales = line.qty_delivered * line.price_unit * (1 - (line.discount or 0.0) / 100.0)
