# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    sale_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Sale Price Based on")
    purchase_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Purchase Price Based on")
