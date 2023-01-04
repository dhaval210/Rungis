from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    so_commitment_date = fields.Datetime(related="order_id.commitment_date", store=True)
