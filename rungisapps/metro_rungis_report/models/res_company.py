# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    cw_product_highlight = fields.Boolean(string='Cw Product Highlight',
                                default=False)
    operation_filters = fields.Many2many('stock.picking.type',
                                string='Picking/Operation Type')
    

