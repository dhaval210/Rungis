from odoo import api, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        block_exceeding = params.get_param(
            'metro_block_exceeding_qty_done.block_exceeding_qty'
        )
        if block_exceeding == 'True':
            filter_id = params.get_param(
                'metro_block_exceeding_qty_done.block_qty_filter_id'
            )
            filter_domain = self.env['ir.filters'].search([
                ('id', '=', filter_id)]
            )._get_eval_domain()

            # check if there is still an open record
            model_rec_ids = self.env['stock.picking.type'].search(
                filter_domain
            )
            if self.picking_type_id.id in model_rec_ids.ids:
                mls = self.mapped('move_line_ids').filtered(
                    lambda x: x.qty_done > x.product_uom_qty
                )
                if len(mls):
                    raise UserError(_("You are not allowed to overpick, please correct your entry"))

        return super().button_validate()
