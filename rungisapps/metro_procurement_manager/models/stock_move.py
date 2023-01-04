from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self, force=False):
        if (
            'force_reservation' not in self.env.context or
            self.env.context.get('force_reservation', False) is False
        ):
            moves = self.filtered(lambda move: move.picking_type_id.block_stock_assignment is False)
            super(StockMove, moves)._action_assign()
        else:
            super(StockMove, self)._action_assign()
        return True
