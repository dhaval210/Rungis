# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier_number = fields.Char(string="Supplier Number", related="user_id.ref")
    order_weight = fields.Float(string="Order Weight", compute='get_order_weight',
                                help="Order weight is calculating with net weight and quantity")
    purchase_ranking = fields.Integer(string='Supplier Ranking', related='partner_id.purchase_ranking',
                                      help="Supplier ranking is calculated based on checking count of purchase order.")
    buyer_ranking = fields.Integer(string='Buyer Ranking', related='user_id.buyer_ranking',
                                   help="Buyer ranking is calculated based on checking count of purchase order.")

    @api.depends('order_line')
    def get_order_weight(self):
        for recd in self:
            order_line = recd.order_line
            total_weight = 0
            for line in order_line:
                net_weight = line.product_id.net_weight
                qty = line.product_qty * line.product_uom.factor_inv
                total_weight += net_weight * qty
            recd.order_weight = total_weight


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    user_id = fields.Many2one('res.users', string="Purchase Representative", related='order_id.user_id', store=True)
    product_reference = fields.Char(string="Article Number", rel="product_id.ref")
    partner_ref = fields.Char(string="Supplier Number", rel="partner_id.ref")
    order_weight = fields.Float(string="Order Weight", compute="get_order_weight",
                                help="Based on net weight and qty")
    order_name = fields.Char(string="Order Name", related="order_id.name")

    def get_order_weight(self):
        for recd in self:
            recd.order_weight = recd.product_id.net_weight * recd.product_qty


