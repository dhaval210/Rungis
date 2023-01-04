from odoo import models
from odoo.tools.float_utils import float_compare, float_is_zero
from itertools import groupby
from operator import itemgetter
from odoo.addons.tis_catch_weight.models import catch_weight


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._action_assign()
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            missing_reserved_cw_uom_quantity = move.product_cw_uom_qty - move.reserved_cw_availability
            missing_reserved_uom_quantity = move.product_uom_qty - move.reserved_availability
            missing_reserved_cw_quantity = move.product_cw_uom._compute_quantity(missing_reserved_cw_uom_quantity,
                                                                                 move.product_id.cw_uom_id,
                                                                                 rounding_method='HALF-UP')
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity,
                                                                           move.product_id.uom_id,
                                                                           rounding_method='HALF-UP')
            if move.location_id.should_bypass_reservation() \
                    or move.product_id.type == 'consu':
                if move.product_id.tracking == 'serial' and (
                        move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    if not missing_reserved_quantity:
                        serial_quantity = missing_reserved_cw_quantity / move.product_uom_qty
                    else:
                        serial_quantity = missing_reserved_cw_quantity / missing_reserved_quantity
                    catch_weight.add_to_context(self, {move.id: serial_quantity})
                else:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                       ml.location_id == move.location_id and
                                                                       ml.location_dest_id == move.location_dest_id and
                                                                       ml.picking_id == move.picking_id and
                                                                       not ml.lot_id and
                                                                       not ml.package_id and
                                                                       not ml.owner_id)
                    if to_update:
                        to_update[0].product_cw_uom_qty += missing_reserved_cw_quantity
                    else:
                        catch_weight.add_to_context(self, {move.id: missing_reserved_cw_quantity})
                        assigned_moves |= move
            else:
                if not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    cw_need = missing_reserved_cw_quantity
                    need = missing_reserved_quantity
                    if float_is_zero(cw_need, precision_rounding=move.product_id.cw_uom_id.rounding):
                        assigned_moves |= move
                        continue
                    available_cw_quantity = self.env['stock.quant'].with_context({'partner': move.picking_id.partner_id.id})._get_available_cw_quantity(move.product_id,
                                                                                               move.location_id)
                    available_quantity = self.env['stock.quant'].with_context({'partner': move.picking_id.partner_id.id})._get_available_quantity(move.product_id,
                                                                                         move.location_id)
                    if available_cw_quantity <= 0:
                        continue
                    taken_cw_quantity = move._update_reserved_cw_quantity(cw_need, available_cw_quantity,
                                                                          need, available_quantity,
                                                                          move.location_id, strict=False)
                    if float_is_zero(taken_cw_quantity, precision_rounding=move.product_id.cw_uom_id.rounding):
                        continue
                    if cw_need == taken_cw_quantity:
                        assigned_moves |= move
                    else:
                        partially_available_moves |= move
                else:
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
                        cw_need = move.cw_product_qty - sum(move.move_line_ids.mapped('cw_product_qty'))
                        need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        available_cw_quantity = self.env['stock.quant'].with_context({'partner': move.picking_id.partner_id.id})._get_available_cw_quantity(
                            move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                            strict=True)
                        available_quantity = self.env['stock.quant'].with_context({'partner': move.picking_id.partner_id.id})._get_available_quantity(
                            move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                            strict=True)
                        if float_is_zero(available_cw_quantity, precision_rounding=move.product_id.cw_uom_id.rounding):
                            continue
                        taken_quantity = move._update_reserved_cw_quantity(cw_need,
                                                                           min(quantity_list[0], available_cw_quantity),
                                                                           need,
                                                                           min(quantity_list[1], available_quantity),
                                                                           location_id, lot_id, package_id, owner_id)

        return super(StockMove, self)._action_assign()
