# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from . import catch_weight


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    product_cw_uom_qty = fields.Float(string='CW Demand', digits=dp.get_precision('Product CW Unit of Measure'))
    cw_qty_done = fields.Float(string='CW Done', compute='_cw_quantity_done_compute', inverse='_cw_quantity_done_set',
                               digits=dp.get_precision('Product CW Unit of Measure'))
    reserved_cw_availability = fields.Float(
        'CW Quantity Reserved', compute='_compute_cw_reserved_availability',
        digits=dp.get_precision('Product CW Unit of Measure'),
        readonly=True, help='CW Quantity that has already been reserved for this move')
    cw_availability = fields.Float(
        'CW Forecasted Quantity', compute='_compute_cw_product_availability',
        digits=dp.get_precision('Product CW Unit of Measure'),
        readonly=True, help='CW Quantity in stock that can still be reserved for this move')
    cw_product_qty = fields.Float(
        'Real CW Quantity', compute='_compute_product_cw_qty', inverse='_set_product_cw_qty',
        digits=0, store=True,
        help='CW Quantity in the default UoM of the product')
    ordered_cw_qty = fields.Float('Ordered CW Quantity', digits=dp.get_precision('Product CW Unit of Measure'))

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMove, self).onchange_product_id()
        if self.product_id._is_cw_product():
            self.product_cw_uom = self.product_id.cw_uom_id.id
            res['domain']['product_cw_uom'] = [('category_id', '=', self.product_id.cw_uom_id.category_id.id)]
        return res

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        self.mapped('purchase_line_id').sudo()._update_received_cw_qty()
        return res

    @api.onchange('product_cw_uom')
    def onchange_product_cw_uom(self):
        if self.product_cw_uom.factor > self.product_id.cw_uom_id.factor:
            return {
                'warning': {
                    'title': "Unsafe unit of measure",
                    'message': _("You are using a unit of measure smaller than the one you are using in "
                                 "order to stock your product. This can lead to rounding problem on reserved quantity. "
                                 "You should use the smaller unit of measure possible in order to valuate your stock or "
                                 "change its rounding precision to a smaller value (example: 0.00001)."),
                }
            }

    @api.multi
    @api.depends('move_line_ids.product_cw_uom_qty', 'move_line_ids.product_cw_uom')
    def _cw_quantity_done_compute(self):
        for move in self:
            cw_qty_done = 0
            for move_line in move._get_move_lines():
                if move_line.product_id._is_cw_product():
                    cw_qty_done += move_line.product_cw_uom._compute_quantity(move_line.cw_qty_done,
                                                                              move.product_cw_uom, round=False)
            move.cw_qty_done = cw_qty_done

    def _cw_quantity_done_set(self):
        quantity_done = self[0].quantity_done
        cw_quantity_done = self[0].cw_qty_done
        for move in self:
            if move.product_id._is_cw_product():
                move_lines = move._get_move_lines()
                if not move_lines:
                    if quantity_done or cw_quantity_done:
                        move_line = self.env['stock.move.line'].create(
                            dict(move._prepare_move_line_vals(), qty_done=quantity_done, cw_qty_done=cw_quantity_done))
                        move.write({'move_line_ids': [(4, move_line.id)]})
                elif len(move_lines) == 1:
                    move_lines[0].qty_done = quantity_done
                    move_lines[0].cw_qty_done = cw_quantity_done
                else:
                    raise UserError(
                        "Cannot set the done cw quantity from this stock move, work directly with the move lines.")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        else:
            res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
            if self.product_id._is_cw_product():
                cw_params = self._context.get('cw_params')
                res.update({'product_cw_uom': self.product_cw_uom and self.product_cw_uom.id})
                if quantity and cw_params:
                    if reserved_quant and reserved_quant.id in cw_params.keys():
                        if self.product_id.tracking == 'serial':
                            quantity_list = cw_params.get(reserved_quant.id)
                            if isinstance(quantity_list, list) and quantity_list:
                                cw_quantity = quantity_list[0]
                                quantity_list.pop(0)
                                cw_uom_quantity = self.product_id.cw_uom_id._compute_quantity(cw_qty,
                                                                                              self.product_cw_uom,
                                                                                              rounding_method='HALF-UP')
                                cw_uom_quantity_back_to_product_uom = self.product_cw_uom._compute_quantity(
                                    cw_uom_quantity,
                                    self.product_id.cw_uom_id,
                                    rounding_method='HALF-UP')
                                rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                                if float_compare(cw_quantity, cw_uom_quantity_back_to_product_uom,
                                                 precision_digits=rounding) == 0:
                                    res.update({'product_cw_uom_qty': cw_uom_quantity})
                                else:
                                    res.update({'product_cw_uom_qty': cw_quantity})

                            else:
                                serial_qty = cw_params.get(reserved_quant.id)
                                cw_uom_quantity = self.product_id.cw_uom_id._compute_quantity(cw_qty,
                                                                                              self.product_cw_uom,
                                                                                              rounding_method='HALF-UP')
                                cw_uom_quantity_back_to_product_uom = self.product_cw_uom._compute_quantity(
                                    cw_uom_quantity,
                                    self.product_id.cw_uom_id,
                                    rounding_method='HALF-UP')
                                rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                                if float_compare(serial_qty, cw_uom_quantity_back_to_product_uom,
                                                 precision_digits=rounding) == 0:
                                    res.update({'product_cw_uom_qty': cw_uom_quantity})
                                else:
                                    res.update({'product_cw_uom_qty': serial_qty})

                        else:
                            cw_qty = cw_params.get(reserved_quant.id)
                            cw_uom_quantity = self.product_id.cw_uom_id._compute_quantity(cw_qty, self.product_cw_uom,
                                                                                          rounding_method='HALF-UP')
                            cw_uom_quantity_back_to_product_uom = self.product_cw_uom._compute_quantity(cw_uom_quantity,
                                                                                                        self.product_id.cw_uom_id,
                                                                                                        rounding_method='HALF-UP')
                            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                            if float_compare(cw_qty, cw_uom_quantity_back_to_product_uom,
                                             precision_digits=rounding) == 0:
                                res.update({'product_cw_uom_qty': cw_uom_quantity})
                            else:
                                res.update({'product_cw_uom_qty': cw_qty})

                    elif self.id in cw_params.keys():
                        cw_qty = cw_params.get(self.id)
                        cw_uom_quantity = self.product_id.cw_uom_id._compute_quantity(cw_qty, self.product_cw_uom,
                                                                                rounding_method='HALF-UP')
                        cw_uom_quantity_back_to_product_uom = self.product_cw_uom._compute_quantity(cw_uom_quantity,
                                                                                              self.product_id.cw_uom_id,
                                                                                              rounding_method='HALF-UP')
                        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        if float_compare(cw_qty, cw_uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                            res.update({'product_cw_uom_qty': cw_uom_quantity})
                        else:
                            res.update({'product_cw_uom_qty': cw_qty})

        return res

    @api.onchange('product_id', 'cw_product_qty')
    def onchange_cw_quantity(self):
        if not self.product_id or self.cw_product_qty < 0.0:
            self.cw_product_qty = 0.0

    def _prepare_procurement_values(self):

        values = super(StockMove, self)._prepare_procurement_values()

        if self.product_cw_uom_qty:
            values.update({
                'cw_qty': self.product_cw_uom_qty,
                'cw_uom': self.product_cw_uom.id,
                'product_cw_uom_qty': self.product_cw_uom_qty,
                'product_cw_uom': self.product_cw_uom.id,
            })
        return values

    @api.model
    def create(self, vals):
        vals['ordered_cw_qty'] = vals.get('product_cw_uom_qty')
        return super(StockMove, self).create(vals)

    @api.one
    @api.depends('product_id', 'product_cw_uom', 'product_cw_uom_qty')
    def _compute_product_cw_qty(self):
        rounding_method = self._context.get('rounding_method', 'UP')
        if self.product_id._is_cw_product():
            self.cw_product_qty = self.product_cw_uom._compute_quantity(self.product_cw_uom_qty,
                                                                        self.product_id.cw_uom_id,
                                                                        rounding_method=rounding_method)

    def _set_product_cw_qty(self):
        raise UserError(_(
            'The requested operation cannot be processed because of a programming error setting '
            'the `cw_product_qty` field instead of the `product_cw_uom_qty`.'))

    @api.one
    @api.depends('state', 'product_id', 'product_cw_uom_qty', 'location_id')
    def _compute_cw_product_availability(self):
        if self.state == 'done':
            self.cw_availability = self.cw_product_qty
        else:
            total_cw_availability = self.env['stock.quant']._get_available_cw_quantity(self.product_id,
                                                                                       self.location_id)
            self.cw_availability = min(self.cw_product_qty, total_cw_availability)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        fields.append('product_cw_uom')
        return fields

    def _create_extra_move(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight') or not self.product_id._is_cw_product():
            return super(StockMove, self)._create_extra_move()
        else:
            extra_move = self
            rounding = self.product_uom.rounding
            cw_rounding = self.product_cw_uom.rounding
            cw_uom_compare = float_compare(self.cw_qty_done, self.product_cw_uom_qty, precision_rounding=cw_rounding)
            uom_compare = float_compare(self.quantity_done, self.product_uom_qty, precision_rounding=rounding)
            if uom_compare > 0 or (cw_uom_compare > 0 and not self.rule_id and not uom_compare < 0):
                extra_move_quantity = float_round(
                    self.quantity_done - self.product_uom_qty,
                    precision_rounding=rounding,
                    rounding_method='HALF-UP')
                extra_move_cw_quantity = float_round(
                    self.cw_qty_done - self.product_cw_uom_qty,
                    precision_rounding=cw_rounding,
                    rounding_method='HALF-UP')
                extra_move_vals = self._prepare_extra_move_vals(extra_move_quantity)
                extra_move = self.copy(default=extra_move_vals)
                merge_into_self = all(
                    self[field] == extra_move[field] for field in self._prepare_merge_moves_distinct_fields())

                if merge_into_self and extra_move.picking_id:
                    extra_move = extra_move._action_confirm(merge_into=self)
                try:
                    production_id = extra_move.production_id
                    raw_material_production_id = extra_move.raw_material_production_id
                except:
                    production_id = False
                    raw_material_production_id = False
                if merge_into_self and (
                        production_id or raw_material_production_id) and not extra_move_quantity:
                    extra_move = extra_move._action_confirm(merge_into=self)
                    return extra_move
                else:
                    extra_move = extra_move._action_confirm()
                if not merge_into_self or not extra_move.picking_id:
                    for move_line in self.move_line_ids.filtered(lambda ml: ml.qty_done):
                        if float_compare(move_line.cw_qty_done, extra_move_cw_quantity,
                                         precision_rounding=cw_rounding) <= 0:
                            extra_move_cw_quantity -= move_line.cw_qty_done
                        if float_compare(move_line.qty_done, extra_move_quantity, precision_rounding=rounding) <= 0:
                            move_line.move_id = extra_move.id
                            extra_move_quantity -= move_line.qty_done
                        else:
                            quantity_split = float_round(
                                move_line.qty_done - extra_move_quantity,
                                precision_rounding=self.product_uom.rounding,
                                rounding_method='UP')
                            cw_quantity_split = float_round(
                                move_line.cw_qty_done - extra_move_cw_quantity,
                                precision_rounding=self.product_cw_uom.rounding,
                                rounding_method='UP')
                            move_line.qty_done = quantity_split
                            move_line.cw_qty_done = cw_quantity_split
                            move_line.copy(default={'move_id': extra_move.id, 'qty_done': extra_move_quantity,
                                                    'product_uom_qty': 0, 'cw_qty_done': extra_move_cw_quantity,
                                                    'product_cw_uom_qty': 0})
                            extra_move_quantity -= extra_move_quantity
                            extra_move_cw_quantity -= extra_move_cw_quantity
                        if extra_move_quantity == 0.0:
                            break
            return extra_move | self

    def _merge_moves_fields(self):
        res = super(StockMove, self)._merge_moves_fields()
        res.update({
            'product_cw_uom_qty': sum(self.mapped('product_cw_uom_qty')),
        })
        return res

    def _split(self, qty, restrict_partner_id=False):
        res = super(StockMove, self)._split(qty)
        self.with_context(do_not_propagate=True, do_not_unreserve=True, rounding_method='HALF-UP').write(
            {'product_cw_uom_qty': self.cw_qty_done})
        return res

    def _prepare_extra_move_vals(self, qty):
        res = super(StockMove, self)._prepare_extra_move_vals(qty)
        if self.cw_qty_done - self.product_cw_uom_qty > 0:
            extra_move_cw_quantity = self.cw_qty_done - self.product_cw_uom_qty
            res.update({
                'product_cw_uom_qty': extra_move_cw_quantity,
            })
        elif self.cw_qty_done - self.product_cw_uom_qty == 0:
            res.update({
                'product_cw_uom_qty': 0.0,
            })
        return res

    def _prepare_move_split_vals(self, qty):
        res = super(StockMove, self)._prepare_move_split_vals(qty)
        decimal_precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
        if float_compare(self.cw_qty_done, self.product_cw_uom_qty,
                         precision_digits=decimal_precision) < 0:  # Need to do some kind of conversion here
            cw_qty_split = self.product_cw_uom._compute_quantity(self.product_cw_uom_qty - self.cw_qty_done,
                                                                 self.product_id.cw_uom_id, rounding_method='HALF-UP')

            cw_uom_qty = self.product_id.cw_uom_id._compute_quantity(cw_qty_split, self.product_cw_uom,
                                                                     rounding_method='HALF-UP')
            if float_compare(cw_qty_split, self.product_cw_uom._compute_quantity(cw_uom_qty, self.product_id.cw_uom_id,
                                                                                 rounding_method='HALF-UP'),
                             precision_digits=decimal_precision) == 0:
                cw_qty = cw_uom_qty
            else:
                cw_qty = cw_qty_split
            res.update({
                'product_cw_uom_qty': cw_qty,
            })
        if float_compare(self.cw_qty_done, self.product_cw_uom_qty, precision_digits=decimal_precision) > 0 and \
                float_compare(self.quantity_done, self.product_uom_qty, precision_digits=decimal_precision) < 0:
            res.update({
                'product_cw_uom_qty': 0,
            })
        return res

    @api.multi
    @api.depends('move_line_ids.cw_product_qty')
    def _compute_cw_reserved_availability(self):
        result = {data['move_id'][0]: data['cw_product_qty'] for data in
                  self.env['stock.move.line'].read_group([('move_id', 'in', self.ids)], ['move_id', 'cw_product_qty'],
                                                         ['move_id'])}
        for rec in self:
            if rec.product_id._is_cw_product() and rec.product_cw_uom:
                rec.reserved_cw_availability = rec.product_id.cw_uom_id._compute_quantity(result.get(rec.id, 0.0),
                                                                                          rec.product_cw_uom,
                                                                                          rounding_method='HALF-UP')

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
                    available_cw_quantity = self.env['stock.quant']._get_available_cw_quantity(move.product_id,
                                                                                               move.location_id)
                    available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id,
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
                        available_cw_quantity = self.env['stock.quant']._get_available_cw_quantity(
                            move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                            strict=True)
                        available_quantity = self.env['stock.quant']._get_available_quantity(
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

    def _update_reserved_cw_quantity(self, cw_need, available_cw_quantity, need, available_quantity, location_id,
                                     lot_id=None, package_id=None,
                                     owner_id=None, strict=True):
        cw_params = self._context.get('cw_params')
        self.ensure_one()
        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        taken_cw_quantity = min(available_cw_quantity, cw_need)
        if not strict:
            taken_quantity_cw_move_uom = self.product_id.cw_uom_id._compute_quantity(taken_cw_quantity, self.product_cw_uom, rounding_method='DOWN')
            taken_cw_quantity = self.product_cw_uom._compute_quantity(taken_quantity_cw_move_uom, self.product_id.cw_uom_id, rounding_method='HALF-UP')

        if self.product_id.tracking == 'serial':
            taken_cw_quantity = available_cw_quantity

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


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                               name, origin, values, group_id)
        if values.get('product_cw_uom', False):
            result['product_cw_uom'] = values['product_cw_uom']
        if values.get('product_cw_uom_qty', False):
            result['product_cw_uom_qty'] = values['product_cw_uom_qty']
        return result
