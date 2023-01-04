# -*- coding: utf-8 -*-

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    custom_internal_ref = fields.Char(
        related='partner_id.ref',
        store=True,
        readonly=True,
        copy=False,
        string='Internal Reference'
    )