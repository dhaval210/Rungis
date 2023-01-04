"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, api


class StockInventory(models.Model):
    """inherit stock module for get report"""
    _inherit = 'stock.inventory'

    @api.multi
    def action_report(self):
        """call report template when click button print report"""
        return self.env.ref(
            'metro_report_inventory_adjustment.metro_report_inventory_adjustment'). \
            report_action(self)
