# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.addons.tis_catch_weight.models import catch_weight


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._action_assign()
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        extra_move_cw_quantity = {}
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            if not (move.location_id.should_bypass_reservation() or move.product_id.type == 'consu'):
                if move.move_orig_ids:
                    move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                    keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                    def _keys_in_sorted(ml):
                        return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                    grouped_move_lines_in = {}
                    for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                        cw_qty_done = 0
                        qty_done = 0
                        for ml in g:
                            cw_qty_done += ml.product_cw_uom._compute_quantity(ml.cw_qty_done, ml.product_id.cw_uom_id)
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_in[k] = [cw_qty_done, qty_done]
                    move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move) \
                        .filtered(lambda m: m.state in ['done']) \
                        .mapped('move_line_ids')
                    # As we defer the write on the stock.move's state at the end of the loop, there
                    # could be moves to consider in what our siblings already took.
                    moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                    moves_out_siblings_to_consider = moves_out_siblings & (assigned_moves + partially_available_moves)
                    reserved_moves_out_siblings = moves_out_siblings.filtered(
                        lambda m: m.state in ['partially_available', 'assigned'])
                    move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped(
                        'move_line_ids')
                    keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                    def _keys_out_sorted(ml):
                        return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                    grouped_move_lines_out = {}
                    for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted),
                                        key=itemgetter(*keys_out_groupby)):
                        cw_qty_done = 0
                        qty_done = 0
                        for ml in g:
                            cw_qty_done += ml.product_cw_uom._compute_quantity(ml.cw_qty_done, ml.product_id.cw_uom_id)
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_out[k] = [cw_qty_done, qty_done]
                    for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted),
                                        key=itemgetter(*keys_out_groupby)):
                        cw_product_qty = sum(
                            self.env['stock.move.line'].concat(*list(g)).mapped('cw_product_qty'))
                        product_qty = grouped_move_lines_out[k] = sum(
                            self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                        grouped_move_lines_out[k] = [cw_product_qty, product_qty]
                    available_move_lines = {}
                    for key in grouped_move_lines_in.keys():
                        available_move_lines[key] = []
                        for lines_in in grouped_move_lines_in[key]:
                            if grouped_move_lines_out.get(key):
                                for lines_out in grouped_move_lines_out.get(key, 0):
                                    available_move_lines[key].append(lines_in - lines_out)
                            else:
                                available_move_lines[key].append(lines_in - 0)
                    # pop key if the quantity available amount to 0
                    available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.cw_product_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id,
                                                     move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(
                                move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                move_line.owner_id)][
                                0] -= move_line.cw_product_qty
                            available_move_lines[(
                                move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                move_line.owner_id)][
                                1] -= move_line.product_qty

                    for (location_id, lot_id, package_id,
                         owner_id), quantity_list in available_move_lines.items():
                        warehouse_id = move.warehouse_id or move.picking_id.picking_type_id.warehouse_id
                        if (warehouse_id and warehouse_id.delivery_steps != 'ship_only' and warehouse_id.company_id.id == 1 and move.rule_id) or (warehouse_id and warehouse_id.delivery_steps == 'ship_only' and warehouse_id.company_id.id == 4 and move.rule_id):
                            # cw_need = quantity_list[0]
                            if extra_move_cw_quantity.get(move.id):
                                if isinstance(extra_move_cw_quantity[move.id],
                                              list):
                                    qtys = extra_move_cw_quantity[move.id]
                                else:
                                    qtys = [extra_move_cw_quantity[move.id]]
                                qtys += [round(quantity_list[0], 4)]
                                extra_move_cw_quantity.update({
                                    move.id: qtys
                                })
                            else:
                                extra_move_cw_quantity[move.id] = round(
                                    quantity_list[0], 4)
                            catch_weight.add_to_context(self, {'extra_move_cw_quantity': extra_move_cw_quantity})
        return super(StockMove, self)._action_assign()

    def _update_reserved_cw_quantity(self, cw_need, available_cw_quantity, need, available_quantity, location_id,
                                     lot_id=None, package_id=None,
                                     owner_id=None, strict=True):
        #  Create or update move lines.
        cw_params = self._context.get('cw_params')
        self.ensure_one()
        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        taken_cw_quantity = min(available_cw_quantity, cw_need)
        if self.product_id.tracking == 'serial':
            taken_cw_quantity = available_cw_quantity
        warehouse_id = self.warehouse_id or self.picking_id.picking_type_id.warehouse_id

        if (warehouse_id and warehouse_id.delivery_steps != 'ship_only' and warehouse_id.company_id.id == 1 and self.rule_id) or (warehouse_id and warehouse_id.delivery_steps == 'ship_only' and warehouse_id.company_id.id == 4 and self.rule_id):
            cw_params = self._context.get('cw_params')
            if (
                cw_params and
                'extra_move_cw_quantity' in cw_params and
                self.id in cw_params.get('extra_move_cw_quantity')
            ):
                extra_move_cw_quantity = cw_params.get('extra_move_cw_quantity')
                cw_quantity = extra_move_cw_quantity.get(self.id, 0.00)
                if isinstance(cw_quantity, list):
                    cw_quantity = cw_quantity.pop(0)
                taken_cw_quantity = cw_quantity
        taken_quantity = min(available_quantity, need)
        quants = []
        try:
            if not float_is_zero(taken_cw_quantity, precision_rounding=self.product_id.cw_uom_id.rounding):
                quants = self.env['stock.quant']._update_reserved_cw_quantity(
                    self.product_id, location_id, taken_cw_quantity, taken_quantity, lot_id=lot_id,
                    package_id=package_id, owner_id=owner_id, strict=strict
                )
        except UserError:
            taken_cw_quantity = 0
        # Find a candidate move line to update or create a new one.
        serial_dict = []
        for reserved_quant, cw_quantity in quants:
            to_update = self.move_line_ids.filtered(lambda m: m.product_id.tracking != 'serial' and
                                                              m.location_id.id == reserved_quant.location_id.id and m.lot_id.id == reserved_quant.lot_id.id and m.package_id.id == reserved_quant.package_id.id and m.owner_id.id == reserved_quant.owner_id.id)
            if to_update:
                to_update[0].with_context(
                    bypass_reservation_update=True).product_cw_uom_qty += self.product_id.cw_uom_id._compute_quantity(
                    cw_quantity, to_update[0].product_cw_uom, rounding_method='HALF-UP')

            else:
                if self.product_id.tracking == 'serial':
                    if cw_params and reserved_quant.id in cw_params.keys():
                        serial_dict = cw_params.get(reserved_quant.id)
                        if not isinstance(serial_dict, list):
                            serial_dict = []
                        serial_dict.append(cw_quantity)
                        catch_weight.add_to_context(self, {reserved_quant.id: serial_dict})
                    else:
                        serial_dict.append(cw_quantity)
                        catch_weight.add_to_context(self, {reserved_quant.id: serial_dict})
                elif self.product_id.tracking == 'lot':
                    catch_weight.add_to_context(self, {reserved_quant.id: cw_quantity})
                else:
                    catch_weight.add_to_context(self, {self.id: cw_quantity})
        return taken_cw_quantity
