# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = "stock.location"

    location_capacity = fields.Float(string='Capacity', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    @api.multi
    def _get_remaining_capacity(self, product_id):
        location_capacity = self.location_capacity
        quant_obj = self.env['stock.quant']
        onhand_qty = quant_obj._get_available_quantity(
            product_id, self)
        qty_res = quant_obj._gather(product_id,
                                    self)
        reserved_qty = sum(qty_res.mapped('reserved_quantity'))
        remaining_capacity = location_capacity - (onhand_qty + reserved_qty)
        return remaining_capacity