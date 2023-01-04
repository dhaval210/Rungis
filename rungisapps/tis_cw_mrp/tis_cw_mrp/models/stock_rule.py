# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, values, bom):
        res = super(StockRule, self)._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, values, bom)
        factor = product_uom._compute_quantity(product_qty,
                                               bom.product_uom_id) / bom.product_qty
        cw_product_qty = bom.cw_product_qty * factor
        res.update({
            'cw_product_qty': cw_product_qty,
            'product_cw_uom_id': bom.product_cw_uom_id.id,
        })
        return res