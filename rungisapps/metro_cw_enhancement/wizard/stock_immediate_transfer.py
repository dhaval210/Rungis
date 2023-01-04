from odoo.addons.tis_catch_weight.wizard.stock_immediate_transfer import StockImmediateTransfer
from odoo import api, _
from odoo.exceptions import UserError


@api.multi
def process(self):
    for picking in self.pick_ids:
        for move in picking.move_lines:
            for move_line in move.move_line_ids:
                if move_line.product_id._is_cw_product():
                    if move_line.product_cw_uom_qty <= 0 and move_line.cw_qty_done <= 0:
                        raise UserError(
                            _(
                                "You cannot validate a transfer if no CW quantities are reserved nor done. To force the transfer, switch in edit mode and encode the CW done quantities."))
                    if move_line.product_cw_uom_qty == 0 and move_line.cw_qty_done > 0:
                        continue
                    move_line.cw_qty_done = move_line.product_cw_uom_qty
                else:
                    move_line.cw_qty_done = 0
    return super(StockImmediateTransfer, self).process()


StockImmediateTransfer.process = process
