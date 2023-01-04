from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    buyer_id = fields.Many2one('res.users', related='order_id.partner_id.buyer_id', string='Buyer', readonly=True, store=True)