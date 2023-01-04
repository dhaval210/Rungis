from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self, force=False):
        if (
            'ignore_reservation' not in self.env.context or
            self.env.context.get('ignore_reservation', False) is False
        ):
            super(StockMove, self)._action_assign()
        else:
            moves = self.filtered(lambda move: move.picking_type_id.code == 'incoming')
            if len(moves) > 0:
                super(StockMove, moves)._action_assign()
        return True
