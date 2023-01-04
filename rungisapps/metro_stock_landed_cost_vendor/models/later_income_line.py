# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaterIncomeLine(models.Model):
    _name = 'later.income.line'
    _description = "Vendor Later Income Lines"

    product_id = fields.Many2one('product.product',
                                 string="Later Income",
                                 domain=[('landed_cost_ok', '=', True)],
                                 required=True)
    percentage = fields.Float(string="Percentage")
    partner_id = fields.Many2one('res.partner', string="Vendor")