# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, _

from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _create_byproduct_move(self, sub_product):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProduction, self)._create_byproduct_move(sub_product)
        Move = self.env['stock.move']
        for production in self:
            source = production.product_id.property_stock_production.id
            product_uom_factor = production.product_uom_id._compute_quantity(
                production.product_qty - production.qty_produced, production.bom_id.product_uom_id)
            qty1 = sub_product.product_qty
            qty1 *= product_uom_factor / production.bom_id.product_qty
            cw_product_uom_factor = production.product_cw_uom_id._compute_quantity(
                production.cw_product_qty - production.cw_qty_produced, production.bom_id.product_cw_uom_id)
            cw_qty1 = sub_product.cw_product_qty
            cw_qty1 *= cw_product_uom_factor / production.bom_id.cw_product_qty
            data = {
                'name': 'PROD:%s' % production.name,
                'date': production.date_planned_start,
                'product_id': sub_product.product_id.id,
                'product_uom_qty': qty1,
                'product_cw_uom_qty': cw_qty1,
                'product_uom': sub_product.product_uom_id.id,
                'product_cw_uom': sub_product.product_cw_uom_id.id,
                'location_id': source,
                'location_dest_id': production.location_dest_id.id,
                'operation_id': sub_product.operation_id.id,
                'production_id': production.id,
                'warehouse_id': production.location_dest_id.get_warehouse().id,
                'origin': production.name,
                'unit_factor': qty1 / (production.product_qty - production.qty_produced),
                'cw_unit_factor': cw_qty1 / (production.cw_product_qty - production.cw_qty_produced),
                'propagate': self.propagate,
                'group_id': self.move_dest_ids and self.move_dest_ids.mapped('group_id')[
                    0].id or self.procurement_group_id.id,
                'subproduct_id': sub_product.id
            }
            move = Move.create(data)
            move._action_confirm()



class MrpProductProduce(models.TransientModel):
    _name = "mrp.product.produce"
    _description = "Record Production"
    _inherit = "mrp.product.produce"

    @api.multi
    def check_finished_move_lots(self):
        res = super(MrpProductProduce, self).check_finished_move_lots()
        by_product_moves = self.production_id.move_finished_ids.filtered(
            lambda m: m.product_id != self.product_id and m.product_id.tracking != 'none' and m.state not in (
            'done', 'cancel'))
        for by_product_move in by_product_moves:
            rounding = by_product_move.product_uom.rounding
            cw_rounding = by_product_move.product_cw_uom.rounding
            quantity = float_round(self.product_qty * by_product_move.unit_factor, precision_rounding=rounding)
            if by_product_move.cw_unit_factor:
                cw_quantity = float_round(self.cw_product_qty * by_product_move.cw_unit_factor,
                                      precision_rounding=cw_rounding)
            else:
                cw_quantity = float_round(self.cw_product_qty * by_product_move.unit_factor,
                                          precision_rounding=cw_rounding)
            serial_cw_quantity = cw_quantity / quantity
            for move_line in by_product_move.move_line_ids:
                if move_line.product_id.tracking == 'lot':
                    move_line.product_cw_uom_qty = cw_quantity
                    move_line.product_cw_uom = by_product_move.product_cw_uom.id
                    move_line.cw_qty_done = cw_quantity
                else:
                    move_line.product_cw_uom_qty = serial_cw_quantity
                    move_line.product_cw_uom = by_product_move.product_cw_uom.id
                    move_line.cw_qty_done = serial_cw_quantity
        return res
