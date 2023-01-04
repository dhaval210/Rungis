from odoo import api, fields, models


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.multi
    def write(self, vals):
        for rec in self:
            if (
                'qty_done' in vals and
                rec.result_package_id is not False and
                rec.package_id == rec.result_package_id and
                rec.product_uom_qty != vals['qty_done'] and
                rec.picking_id.picking_type_code != "incoming"
            ):
                rec.result_package_id = False
        return super().write(vals)
