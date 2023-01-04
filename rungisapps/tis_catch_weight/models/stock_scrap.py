# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools import float_compare

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM', states={'done': [('readonly', True)]})
    scrap_cw_qty = fields.Float(string='CW Quantity', states={'done': [('readonly', True)]})

    def _prepare_move_values(self):

        res = super(StockScrap, self)._prepare_move_values()
        res.update({
            'product_cw_uom': self.product_cw_uom.id,
            'product_cw_uom_qty': self.scrap_cw_qty,

        })
        for values in res['move_line_ids']:
            values[2].update({
                'product_cw_uom': self.product_cw_uom.id,
                'cw_qty_done': self.scrap_cw_qty,
            })
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):

        res = super(StockScrap, self).onchange_product_id()
        self.product_cw_uom = self.product_id.cw_uom_id.id
        return res

    def action_validate(self):
        self.ensure_one()
        if self.product_id.type != 'product':
            return self.do_scrap()
        precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
        available_cw_qty = sum(self.env['stock.quant']._gather(self.product_id,
                                                            self.location_id,
                                                            self.lot_id,
                                                            self.package_id,
                                                            self.owner_id,
                                                            strict=True).mapped('cw_stock_quantity'))
        scrap_cw_qty = self.product_cw_uom._compute_quantity(self.scrap_cw_qty, self.product_id.cw_uom_id)
        if float_compare(available_cw_qty, scrap_cw_qty, precision_digits=precision) >= 0:
            return super(StockScrap, self).action_validate()
        else:
            return {
                'name': _('Insufficient Quantity'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.warn.insufficient.qty.scrap',
                'view_id': self.env.ref('stock.stock_warn_insufficient_qty_scrap_form_view').id,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_location_id': self.location_id.id,
                    'default_scrap_id': self.id
                },
                'target': 'new'
            }
