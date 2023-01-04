# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PackingDetails(models.Model):
    _name = "packing.details"
    _rec_name = "order_id"

    order_id = fields.Many2one('sale.order', 'Order Reference')
    message_info = fields.Text(string='Message')
    pack_operation = fields.Char(string='Operations')
    time_stamp = fields.Char(string='Time')
    line_ids = fields.One2many('packing.details.line', 'packing_id')

class PackingDetailsLine(models.Model):
    _name = "packing.details.line"

    packing_id = fields.Many2one("packing.details")
    product_id = fields.Many2one(
        "product.product",
        string="Product"
    )
    qty_ordered = fields.Float(string="Ordered Quantity")
    qty_done = fields.Float("Delivered Quantity")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    