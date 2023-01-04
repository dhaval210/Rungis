# -*- coding: utf-8 -*-

from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    requisition_id = fields.Many2one(
        'purchase.requisition',
        string='Requisitions', 
    )
