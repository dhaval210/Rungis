# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, _


class MrpStockReport(models.TransientModel):
    _inherit = 'stock.traceability.report'

    @api.model
    def _cw_quantity_to_str(self, from_uom, to_uom, qty):
        cw_qty = from_uom._compute_quantity(qty, to_uom, rounding_method='HALF-UP')
        return self.env['ir.qweb.field.float'].value_to_html(cw_qty,
                                                             {'decimal_precision': 'Product CW Unit of Measure'})

    def _make_dict_move(self, level, parent_id, move_line, unfoldable=False):
        res = super(MrpStockReport, self)._make_dict_move(level, parent_id, move_line, unfoldable)
        for data in res:
            if move_line.product_id._is_cw_product():
                data.update({
                    'product_cw_qty_uom': "%s %s" % (
                        self._cw_quantity_to_str(move_line.product_cw_uom, move_line.product_id.cw_uom_id,
                                                 move_line.cw_qty_done),
                        move_line.product_id.cw_uom_id.name),
                })
        return res

    @api.model
    def _final_vals_to_lines(self, final_vals, level):
        lines = super(MrpStockReport, self)._final_vals_to_lines(final_vals, level)
        n = 0
        for i in range(0, len(final_vals)):
            lines[n]['columns'].append(final_vals[n].get('product_cw_qty_uom', 0))
            n += 1
        return lines
