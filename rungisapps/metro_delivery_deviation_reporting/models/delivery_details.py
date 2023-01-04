# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, fields


class SaleOrderData(models.Model):
    """inherit base for get customer for adding boolean"""
    _name = 'packing.details'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', 'Order Reference')
    message_info = fields.Text(string='Message')
    pack_operation = fields.Char(string='Pack Operation')
    time_stamp = fields.Char(string='Time')
    line_id = fields.One2many('packing.details.line', 'order_id')


class SaleOrderDataLine(models.Model):
    _name = 'packing.details.line'

    order_id = fields.Many2one('packing.details')
    product_id = fields.Many2one('product.product', string='Product ',
                                 store=True)
    qty_ordered = fields.Float(string='Quantity Ordered')
    qty_done = fields.Float('Quantity Done')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')

