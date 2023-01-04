# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class DeliveryTime(models.Model):
    _inherit = "sale.order"

    truck = fields.Char(string="Truck ID", copy=False)
