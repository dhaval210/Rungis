from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def unlink_moves_with_ref_po(self):
        self.with_context(prefetch_fields=False).mapped('move_line_ids').unlink()
        models.Model.unlink(self.with_context(prefetch_fields=False))

