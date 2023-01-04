# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = "account.payment"

    truck = fields.Char(compute="_compute_truck",string="Truck ID", readonly='True', store=True)

    @api.multi
    @api.depends('invoice_ids')
    def _compute_truck(self):
        for record in self:
            truck = record.mapped('invoice_ids.invoice_line_ids.sale_line_ids.order_id.truck')
            if truck:
                record.truck = truck[0]
