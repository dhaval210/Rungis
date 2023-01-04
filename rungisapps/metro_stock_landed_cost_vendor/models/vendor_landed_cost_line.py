# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VendorLandedCostLine(models.Model):
    _name = 'vendor.landed.cost.line'
    _description = "Vendor Landed Cost Lines"

    product_id = fields.Many2one('product.product',
                                 string="Landed Cost",
                                 domain=[('landed_cost_ok', '=', True)],
                                 required=True)
    percentage = fields.Float(string="Percentage")
    partner_id = fields.Many2one('res.partner', string="Vendor")