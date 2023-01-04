from odoo import models, fields, api


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
        res = super(StockImmediateTransfer, self).process()
        for picking in self.pick_ids:
            for move in picking.move_lines:
                for move_line in move.move_line_ids:
                    move_line.cw_qty_done = move_line.product_cw_uom_qty
        return res






















