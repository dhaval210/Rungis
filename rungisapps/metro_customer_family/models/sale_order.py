# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_family_id = fields.Many2one('partner.family', string="Customer Family",
                                        related='partner_id.partner_family_id', readonly=True, store=True)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    partner_family_id = fields.Many2one('partner.family', string="Customer Family",
                                        related='order_partner_id.partner_family_id', readonly=True, store=True)
