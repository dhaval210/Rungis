# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<https://technaureus.com/>).

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from datetime import datetime, timedelta


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cw_mrp_product_qty = fields.Float('CW Manufactured', compute='_compute_mrp_product_cw_qty')


    def _compute_mrp_product_cw_qty(self):
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        domain = [('state', '=', 'done'), ('product_id', 'in', self.ids), ('date_planned_start', '>', date_from)]
        read_group_res = self.env['mrp.production'].read_group(domain, ['product_id', 'product_cw_uom_qty'],
                                                               ['product_id'])
        mapped_data = dict([(data['product_id'][0], data['product_cw_uom_qty']) for data in read_group_res])
        for product in self:
            product.cw_mrp_product_qty = float_round(mapped_data.get(product.id, 0),
                                                     precision_rounding=product.cw_uom_id.rounding)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cw_mrp_product_qty = fields.Float('CW Manufactured', compute='_compute_mrp_product_cw_qty')

    @api.one
    def _compute_mrp_product_cw_qty(self):
        self.cw_mrp_product_qty = float_round(sum(self.mapped('product_variant_ids').mapped('cw_mrp_product_qty')),
                                              precision_rounding=self.cw_uom_id.rounding)