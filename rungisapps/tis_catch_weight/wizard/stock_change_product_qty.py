# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, fields, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ProductChangeQuantity(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    new_cw_quantity = fields.Float(
        'New CW Quantity on Hand', default=0,
        digits=dp.get_precision('Product CW Unit of Measure'), required=True, )

    def _action_start_line(self):
        res = super(ProductChangeQuantity, self)._action_start_line()
        product = self.product_id.with_context(location=self.location_id.id)
        cw_th_qty = product.cw_qty_available
        res.update({
            'cw_product_qty': self.new_cw_quantity,
            'product_cw_uom': self.product_id.cw_uom_id.id,
            'theoretical_cw_qty': cw_th_qty,
        })
        return res

    @api.constrains('new_cw_quantity')
    def check_new_cw_quantity(self):
        if any(wizard.new_cw_quantity < 0 for wizard in self):
            raise UserError(_('CW Quantity cannot be negative.'))

    @api.onchange('location_id', 'product_id')
    def cw_onchange_location_id(self):
        super(ProductChangeQuantity, self).onchange_location_id()
        if self.location_id and self.product_id:
            availability = self.product_id.with_context(compute_child=False)._product_available()
            self.new_cw_quantity = availability[self.product_id.id]['cw_qty_available']

    def change_product_qty(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(ProductChangeQuantity, self).change_product_qty()
        else:
            if self.product_id.catch_weight_ok and self.new_cw_quantity == 0 and self.new_quantity != 0:
                raise UserError(_("Please enter the CW Quantity"))
            if self.new_cw_quantity != 0 and self.new_quantity == 0:
                raise UserError(_("Please enter the Quantity"))
            return super(ProductChangeQuantity, self).change_product_qty()
