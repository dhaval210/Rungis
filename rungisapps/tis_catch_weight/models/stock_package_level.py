# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from itertools import groupby
from operator import itemgetter


class StockPackageLevel(models.Model):
    _inherit = 'stock.package_level'

    def _set_is_done(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockPackageLevel, self)._set_is_done()
        for package_level in self:
            if package_level.is_done:
                if not package_level.is_fresh_package:
                    for quant in package_level.package_id.quant_ids:
                        corresponding_ml = package_level.move_line_ids.filtered(
                            lambda ml: ml.product_id == quant.product_id and ml.lot_id == quant.lot_id)
                        if corresponding_ml:
                            corresponding_ml[0].qty_done = corresponding_ml[0].qty_done + quant.quantity
                            if corresponding_ml[0].product_id._is_cw_product():
                                corresponding_ml[0].cw_qty_done = corresponding_ml[
                                                                      0].cw_qty_done + quant.cw_stock_quantity
                        else:
                            corresponding_move = package_level.move_ids.filtered(
                                lambda m: m.product_id == quant.product_id)[:1]
                            self.env['stock.move.line'].create({
                                'location_id': package_level.location_id.id,
                                'location_dest_id': package_level.location_dest_id.id,
                                'picking_id': package_level.picking_id.id,
                                'product_id': quant.product_id.id,
                                'qty_done': quant.quantity,
                                'cw_qty_done': quant.cw_stock_quantity if quant.product_id._is_cw_product() else 0,
                                'product_uom_id': quant.product_id.uom_id.id,
                                'product_cw_uom': quant.product_id.cw_uom_id.id if quant.product_id._is_cw_product() else 0,
                                'lot_id': quant.lot_id.id,
                                'package_id': package_level.package_id.id,
                                'result_package_id': package_level.package_id.id,
                                'package_level_id': package_level.id,
                                'move_id': corresponding_move.id,
                            })
            else:
                package_level.move_line_ids.filtered(lambda ml: ml.product_qty == 0).unlink()
                package_level.move_line_ids.filtered(lambda ml: ml.product_qty != 0).write(
                    {'qty_done': 0, 'cw_qty_done': 0})

    def _generate_moves(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockPackageLevel, self)._generate_moves()
        for package_level in self:
            if package_level.package_id:
                for quant in package_level.package_id.quant_ids:
                    self.env['stock.move'].create({
                        'picking_id': package_level.picking_id.id,
                        'name': quant.product_id.display_name,
                        'product_id': quant.product_id.id,
                        'product_uom_qty': quant.quantity,
                        'product_cw_uom_qty': quant.cw_stock_quantity if quant.product_id._is_cw_product() else 0,
                        'product_uom': quant.product_id.uom_id.id,
                        'product_cw_uom': quant.product_id.cw_uom_id.id if quant.product_id._is_cw_product() else 0,
                        'location_id': package_level.location_id.id,
                        'location_dest_id': package_level.location_dest_id.id,
                        'package_level_id': package_level.id,
                    })

