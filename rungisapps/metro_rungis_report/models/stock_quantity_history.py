# -*- coding: utf-8 -*-
from odoo import models, api


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    @api.multi
    def button_export_html(self):
        res = super(StockQuantityHistory, self).button_export_html()
        report_id = res['context']['active_ids']
        report = self.env['report.stock.inventory.valuation.report'].browse(report_id)
        report.update(
            {
                'warehouse_ids': [(6, 0, self.warehouse_ids.ids)]
            }
        )
        return res

    def _export(self, report_type):
        res = super(StockQuantityHistory, self)._export(report_type)
        report_id = res['context']['active_ids']
        report = self.env['report.stock.inventory.valuation.report'].browse(report_id)
        report.update(
            {
                'warehouse_ids': [(6, 0, self.warehouse_ids.ids)]
            }
        )
        return res

