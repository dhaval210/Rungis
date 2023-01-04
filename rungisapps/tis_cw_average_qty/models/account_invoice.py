# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>)

from odoo import models, fields, api, _


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id', 'quantity', 'uom_id')
    def _onchange_average_cw_quantity(self):
        if self.product_id._is_cw_product():
            if self.purchase_line_id or self.sale_line_ids or self.origin or self.purchase_id:
                return
            else:
                if self.uom_id == self.product_id.uom_id and self.product_id.average_cw_quantity:
                    self.product_cw_uom_qty = self.quantity * self.product_id.average_cw_quantity
                else:
                    if self.product_id.average_cw_quantity:
                        product_uom_qty = self.uom_id._compute_quantity(self.quantity, self.product_id.uom_id)
                        self.product_cw_uom_qty = product_uom_qty * self.product_id.average_cw_quantity
        else:
            self.product_cw_uom_qty = 0
