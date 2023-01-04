from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _check_backorder(self):
        res = super(StockPicking, self)._check_backorder()
        move_lines = self.mapped('move_lines')
        move_lines_result = []
        for move in move_lines:
            if move.product_id.catch_weight_ok:
                if move.special_wishes:
                    if not move.reserved_availability and not move.reserved_cw_availability:
                        move_lines_result.append(move)
                else:
                    if (move.product_uom_qty != move.reserved_availability and \
                    move.product_cw_uom_qty != move.reserved_cw_availability) or move.quantity_done:
                        move_lines_result.append(move)
            else:
                if move.special_wishes:
                    if not move.reserved_availability:
                        move_lines_result.append(move)
                else:
                    if move.product_uom_qty != move.reserved_availability or move.quantity_done:
                        move_lines_result.append(move)
        if not move_lines_result:
             res = False
        return res

    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        res = super(StockPicking, self)._create_backorder(backorder_moves)
        move_lines = res.mapped('move_lines')
        move_lines_wish = []
        for move in move_lines:
            if move.product_id.catch_weight_ok:
                if move.special_wishes and move.reserved_availability and move.reserved_cw_availability:
                    move_lines_wish.append(move)
            else:
                if move.special_wishes and move.reserved_availability:
                    move_lines_wish.append(move)
        if len(move_lines_wish) == len(move_lines):
            if res:
                res.state = 'cancel'
        else:
            for line in move_lines_wish:
                line.state = 'draft'
                line.unlink()
        return res

