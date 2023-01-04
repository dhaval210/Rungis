# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _get_cw_qty_procurement(self):
        purchase_lines_sudo = self.sudo().purchase_line_ids
        if purchase_lines_sudo.filtered(lambda r: r.state != 'cancel'):
            cw_qty = 0.0
            for po_line in purchase_lines_sudo.filtered(lambda r: r.state != 'cancel'):
                cw_qty += po_line.product_cw_uom.product_cw_uom_qty(po_line.product_cw_uom_qty, self.product_cw_uom,
                                                                    rounding_method='HALF-UP')
            return cw_qty

        else:
            return super(SaleOrderLine, self)._get_cw_qty_procurement()
