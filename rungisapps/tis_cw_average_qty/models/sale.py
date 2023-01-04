# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id._is_cw_product():
            if self.product_uom == self.product_id.uom_id and self.product_id.average_cw_quantity:
                self.product_cw_uom_qty = self.product_uom_qty * self.product_id.average_cw_quantity
            else:
                if self.product_id.average_cw_quantity:
                    product_uom_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
                    self.product_cw_uom_qty = product_uom_qty * self.product_id.average_cw_quantity
        else:
            self.product_cw_uom_qty = 0
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super(SaleOrderLine, self).product_uom_change()
        if self.product_id._is_cw_product():
            if self.product_uom == self.product_id.uom_id:
                self.product_cw_uom_qty = self.product_uom_qty * self.product_id.average_cw_quantity
            else:
                product_uom_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
                self.product_cw_uom_qty = product_uom_qty * self.product_id.average_cw_quantity
        else:
            self.product_cw_uom_qty = 0
