# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    no_expiry = fields.Boolean(string='No Expiry Date', compute='_compute_no_expiry', readonly=True, store=True)

    @api.depends('life_time', 'use_time', 'removal_time', 'alert_time')
    def _compute_no_expiry(self):
        for product in self:
            product.no_expiry = not any([product.life_time, product.use_time, product.removal_time, product.alert_time])
