# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    expired_product_type_id = fields.Many2one('stock.picking.type', 'Expired Product Picking Type')
