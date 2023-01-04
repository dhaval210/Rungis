# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).


from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cart_cw_quantity = fields.Integer(compute='_compute_cart_info_cw', string='Cart CW Quantity')

    @api.multi
    @api.depends('website_order_line.product_cw_uom_qty', 'website_order_line.product_id')
    def _compute_cart_info_cw(self):
        for order in self:
            order.cart_cw_quantity = int(sum(order.mapped('website_order_line.product_cw_uom_qty')))
