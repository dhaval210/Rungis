# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        msg = ''
        for line in self.order_line:
            if line.product_id._is_cw_product():
                if line.product_cw_uom and line.product_id.cw_uom_id:
                    if line.product_cw_uom.category_id.id != line.product_id.cw_uom_id.category_id.id:
                        msg += "The CW-UOM %s defined on the order line doesn\'t belong to the same category " \
                               "than the CW-UOM %s defined on the %s. They should belong to the same " \
                               "category.\n " % (
                                   line.product_cw_uom.name, line.product_id.cw_uom_id.name,
                                   line.product_id.display_name)
            else:
                line.product_cw_uom = False
        if msg:
            raise UserError(_(msg))
        return super(PurchaseOrder, self).button_confirm()
