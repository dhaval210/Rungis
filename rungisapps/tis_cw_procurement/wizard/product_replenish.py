# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd(<http://technaureus.com/>).

from odoo import api, fields, models, _


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'

    catch_weight_ok = fields.Boolean(related='product_id.catch_weight_ok')
    product_cw_uom_category_id = fields.Many2one('uom.category', string='CW Uom Category',
                                                 related='product_id.cw_uom_id.category_id', readonly=True,
                                                 required=True)
    product_cw_uom_id = fields.Many2one('uom.uom', string='Unit of measure', required=True)
    cw_quantity = fields.Float('CW Quantity', default=0, required=True)

    @api.model
    def default_get(self, fields):
        res = super(ProductReplenish, self).default_get(fields)
        product_tmpl = self.env['product.template'].browse(res['product_tmpl_id'])
        if 'product_cw_uom_id' in fields:
            res['product_cw_uom_id'] = product_tmpl.cw_uom_id.id
        return res

    def _prepare_run_values(self):
        values = super(ProductReplenish, self)._prepare_run_values()
        cw_uom_reference = self.product_id.cw_uom_id
        self.cw_quantity = self.product_cw_uom_id._compute_quantity(self.cw_quantity, cw_uom_reference)
        values.update({
            'cw_qty': self.cw_quantity,
            'cw_uom': cw_uom_reference.id
        })
        return values
