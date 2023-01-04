# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        if not res and self.pick_ids.call_pdf_report() != None:
            return {
                'type': 'ir.actions.act_multi',
                'actions': [
                    {'type': 'ir.actions.act_window_close'},
                    self.pick_ids.call_pdf_report(),
                    res,
                ]
            }
        else:
            return res


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        res = super(StockBackorderConfirmation, self).process()
        if not res:
            return {
                'type': 'ir.actions.act_multi',
                'actions': [
                    {'type': 'ir.actions.act_window_close'},
                    self.pick_ids.call_pdf_report(),
                ]
            }
        else:
            return res

    def process_cancel_backorder(self):
        res = super(StockBackorderConfirmation,
                    self).process_cancel_backorder()
        if not res:
            return {
                'type': 'ir.actions.act_multi',
                'actions': [
                    {'type': 'ir.actions.act_window_close'},
                    self.pick_ids.call_pdf_report(),
                ]
            }
        else:
            return res
