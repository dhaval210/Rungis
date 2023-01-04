# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = "stock.picking"

    # shipment_sale_order_id = fields.Many2one('sale.order', string="Linked Sale Order", compute='_compute_picking_so_id', readonly='True', store='True')
    truck = fields.Char(string="Truck ID", related='sale_id.truck', readonly='True', store='True')
    customer_delivery_date = fields.Datetime(string="Customer Delivery Date", compute='_compute_customer_delivery_date', readonly='True', store='True',
                                             help='requested_date from the SO if filled, else commitment_date')

    @api.multi
    @api.depends('sale_id.commitment_date', 'sale_id.commitment_date')
    def _compute_customer_delivery_date(self):
        for record in self:
            record.customer_delivery_date = record.sale_id.commitment_date or record.sale_id.expected_date
