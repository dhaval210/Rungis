# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields
from odoo.addons import decimal_precision as dp


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    reordering_based_on = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], default='uom', required='1')
    product_cw_uom = fields.Many2one('uom.uom', 'Product CW Unit of Measure', related='product_id.cw_uom_id',
                                     readonly=True, required=True)
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    product_min_cw_qty = fields.Float(
        'Minimum CW Quantity', digits=dp.get_precision('Product CW Unit of Measure'),
        help="When the virtual stock goes below the Min CW Quantity specified for this field, Odoo generates "
             "a procurement to bring the forecasted quantity to the Max CW Quantity.")
    product_max_cw_qty = fields.Float(
        'Maximum CW Quantity', digits=dp.get_precision('Product Unit of Measure'),
        help="When the virtual stock goes below the Min CW Quantity, Odoo generates "
             "a procurement to bring the forecasted quantity to the Quantity specified as Max CW Quantity.")

    def _cw_quantity_in_progress(self):
        res = dict(self.mapped(lambda x: (x.id, 0.0)))
        for poline in self.env['purchase.order.line'].search(
                [('state', 'in', ('draft', 'sent', 'to approve')), ('orderpoint_id', 'in', self.ids)]):
            res[poline.orderpoint_id.id] += poline.product_cw_uom._compute_quantity(poline.product_cw_uom_qty,
                                                                                    poline.orderpoint_id.product_cw_uom,
                                                                                    round=False)
        return res
