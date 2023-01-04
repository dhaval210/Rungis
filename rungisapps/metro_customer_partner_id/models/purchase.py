# -*- coding: utf-8 -*-

from odoo import models, fields


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    custom_internal_ref = fields.Char(
        related='partner_id.ref', 
        store=True, 
        readonly=True, 
        copy=False, 
        string='Internal Reference'
    )
