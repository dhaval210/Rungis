# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    @api.onchange('quantity', 'uom_id')
    def _onchange_quantity(self):
        if self.product_id._is_cw_product():
            if self.uom_id == self.product_id.uom_id:
                self.cw_quantity = self.quantity * self.product_id.average_cw_quantity
            else:
                quantity = self.uom_id._compute_quantity(self.product_qty, self.product_id.uom_id)
                self.cw_quantity = quantity * self.product_id.average_cw_quantity
            if self.quantity > 0 and self.cw_quantity > 0:
                warning_mess = self.product_id.check_deviation_warning(self.cw_quantity, self.quantity, self.uom_id,
                                                                       self.cw_uom_id)
                return {'warning': warning_mess}

    @api.onchange('cw_quantity', 'cw_uom_id')
    def _onchange_cw_quantity(self):
        if self.product_id._is_cw_product():
            if self.quantity > 0 and self.cw_quantity > 0:
                warning_mess = self.product_id.check_deviation_warning(self.cw_quantity, self.quantity,
                                                                       self.uom_id, self.cw_uom_id)
                return {'warning': warning_mess}
