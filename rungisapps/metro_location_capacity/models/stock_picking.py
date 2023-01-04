# -*- coding: utf-8 -*-

from odoo import models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        for move in self.move_ids_without_package:
            move.action_show_details()
            self.move_line_ids = move.move_line_ids
        return super(StockPicking, self).button_validate()
