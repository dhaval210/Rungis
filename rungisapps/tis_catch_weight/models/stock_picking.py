# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):

        for line in self.move_lines:
            if line.product_id._is_cw_product():
                if line.quantity_done != 0 and line.cw_qty_done == 0:
                    raise UserError(_("Enter the CW Done quantity for the product %r.") % (line.product_id.name))
                elif line.quantity_done == 0 and line.cw_qty_done != 0:
                    raise UserError(_("Enter the Done quantity for the product %r.") % (line.product_id.name))
            else:
                line.cw_qty_done = 0
                continue
        return super(Picking, self).button_validate()

    def _get_overprocessed_stock_moves(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(Picking, self)._get_overprocessed_stock_moves()
        self.ensure_one()
        result = self.move_lines.filtered(
            lambda move: move.product_cw_uom_qty != 0 and float_compare(move.cw_qty_done, move.product_cw_uom_qty,
                                                                        precision_rounding=move.product_cw_uom.rounding) == 1
        )
        if not result:
            return super(Picking, self)._get_overprocessed_stock_moves()
        else:
            return result
