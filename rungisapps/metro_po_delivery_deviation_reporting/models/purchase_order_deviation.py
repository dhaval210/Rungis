# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrderDeviation(models.Model):
    _name = "purchase.order.deviation"
    _rec_name = "order_id"

    order_id = fields.Many2one(
        "purchase.order", "Order reference"
    )
    message = fields.Text()
    time_stamp = fields.Datetime(
        string="Time of reporting"
    )
    order_schedule = fields.Datetime(
        related="order_id.date_planned",
        string="Planned Delivery"
    )
    order_vendor = fields.Many2one(
        "res.partner",
        related="order_id.partner_id",
        store=True
    )
    responsible = fields.Many2one(
        "res.users",
        related="order_id.user_id",
        store=True
    )
    line_ids = fields.One2many(
        "purchase.order.deviation.line", "deviation_id"
    )

class PurchaseOrderDeviationLine(models.Model):
    _name = "purchase.order.deviation.line"

    deviation_id = fields.Many2one(
        "purchase.order.deviation", "Inbound deviation message"
    )
    product_id = fields.Many2one(
        "product.product", "Product"
    )
    qty_ordered = fields.Float(string="Ordered quantity")
    qty_done = fields.Float(string="Delivered quantity")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
