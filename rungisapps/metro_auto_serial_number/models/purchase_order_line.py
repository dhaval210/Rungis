"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, api, fields


class PurchaseOrderLine(models.Model):
    """inherit purchase order line to add serial number"""
    _inherit = 'purchase.order.line'

    serial_number = fields.Integer(compute='_get_serial_number', store=True)

    @api.depends('sequence', 'order_id')
    def _get_serial_number(self):
        for order in self.mapped('order_id'):
            for index, list_order in enumerate(order.order_line):
                list_order.serial_number = index + 1
