# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class Uom(models.Model):
    _inherit = 'uom.uom'

    @api.multi
    def _compute_price(self, price, to_unit):
        cw_params = self._context.get('cw_params')
        if cw_params and 'cw_product_uom' in cw_params and 'cw_to_uom' in cw_params:
            cw_product_uom = cw_params.get('cw_product_uom')
            to_unit = cw_params.get('cw_to_uom')
            cw_product_uom.ensure_one()
            if not cw_product_uom or not price or not to_unit or cw_product_uom == to_unit:
                return price
            if cw_product_uom.category_id.id != to_unit.category_id.id:
                return price
            amount = price * cw_product_uom.factor
            if to_unit:
                amount = amount / to_unit.factor
            return amount
        else:
            return super(Uom, self)._compute_price(price, to_unit)
