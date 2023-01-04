from odoo import api, fields, models


class ModuleName(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        for pick in self:
            for ml in pick.move_line_ids.filtered(
                lambda m: m.result_package_id is not False and
                m.package_id == m.result_package_id and
                m.qty_done != m.product_uom_qty and
                m.qty_done > 0
            ):
                ml.result_package_id = False
        return super().button_validate()
