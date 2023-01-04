# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id._is_cw_product():
            if self.product_uom == self.product_id.uom_id:
                self.product_cw_uom_qty = self.product_qty * self.product_id.average_cw_quantity
            else:
                product_uom_qty = self.product_uom._compute_quantity(self.product_qty, self.product_id.uom_id)
                self.product_cw_uom_qty = product_uom_qty * self.product_id.average_cw_quantity
        else:
            self.product_cw_uom_qty = 0
        return res

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return
        if self.product_id._is_cw_product():
            if self.product_uom == self.product_id.uom_id and self.product_id.average_cw_quantity:
                self.product_cw_uom_qty = self.product_qty * self.product_id.average_cw_quantity
            else:
                if self.product_id.average_cw_quantity:
                    product_uom_qty = self.product_uom._compute_quantity(self.product_qty, self.product_id.uom_id)
                    self.product_cw_uom_qty = product_uom_qty * self.product_id.average_cw_quantity
        else:
            self.product_cw_uom_qty = 0
