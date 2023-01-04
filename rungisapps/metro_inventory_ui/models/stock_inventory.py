from odoo import models, api, _
from odoo.exceptions import UserError


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.model_create_multi
    def create(self, vals):
        state = self.state
        res = super(StockInventory, self).create(vals)
        self._check_required_lots(state)
        return res

    @api.multi
    def write(self, vals):
        state = self.state
        res = super(StockInventory, self).write(vals)
        self._check_required_lots(state)
        return res

    @api.multi
    def _check_required_lots(self, state):
        for r in self:
            # List of product names with missing lot
            lines_missing_lot = []
            for line in r.line_ids:
                if (
                    line.product_tracking == "lot" and
                    line.prod_lot_id.id is False and
                    state != 'draft' and
                    (
                        (line.product_qty > 0 or line.theoretical_qty > 0) or
                        line.discrepancy_qty != 0
                    )
                ):
                    lines_missing_lot.append(line.product_id.name)
            if len(lines_missing_lot) > 0:
                msg = "Lot # is missing for:"
                for name in lines_missing_lot:
                    msg += ("\n  * " + name )
                raise UserError(_(msg))


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super(StockInventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)

        if "preset_reason_id" in res:
            if res["preset_reason_id"] > 0:
                reason = self.env["stock.inventory.line.reason"].browse(res["preset_reason_id"])
                res["origin"] = reason.description

        return res
