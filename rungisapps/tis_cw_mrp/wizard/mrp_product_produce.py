# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from datetime import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.model
    def default_get(self, fields):
        res = super(MrpProductProduce, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            production = self.env['mrp.production'].browse(self._context['active_id'])
            todo_uom = production.product_cw_uom_id.id
            main_product_moves = production.move_finished_ids.filtered(
                lambda x: x.product_id.id == production.product_id.id)
            todo_quantity = production.cw_product_qty - sum(main_product_moves.mapped('cw_qty_done'))
            todo_quantity = todo_quantity if (todo_quantity > 0) else 0
            if 'product_cw_uom_id' in fields:
                res['product_cw_uom_id'] = todo_uom
            if 'cw_product_qty' in fields:
                res['cw_product_qty'] = todo_quantity
        return res

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    cw_product_qty = fields.Float(string='CW Quantity', digits=dp.get_precision('Product CW Unit of Measure'))
    product_cw_uom_id = fields.Many2one('uom.uom', 'CW Unit of Measure')

    @api.multi
    def do_produce(self):
        mrp_list = []
        for pl in self.produce_line_ids:
            if pl.qty_done:
                if pl.product_id.tracking != 'none' and not pl.lot_id:
                    raise UserError(_('Please enter a lot or serial number for %s !' % pl.product_id.display_name))
                mrp_list.append(pl.cw_qty_done)
                context = self._context.copy()
                if context.get('cw_params'):
                    context['cw_params'].update({'mrp_list': mrp_list})
                else:
                    context['cw_params'] = {'mrp_list': mrp_list}
                self.env.context = context
        res = super(MrpProductProduce, self).do_produce()
        if self.product_id._is_cw_product():
            cw_quantity = self.cw_product_qty
            if float_compare(cw_quantity, 0, precision_rounding=self.product_cw_uom_id.rounding) <= 0:
                raise UserError(
                    _("The production order for '%s' has no CW quantity specified.") % self.product_id.display_name)
            for move in self.production_id.move_finished_ids:
                if move.product_id.tracking == 'none' and move.state not in (
                        'done', 'cancel') and move.product_id._is_cw_product():
                    rounding = move.product_cw_uom.rounding
                    if move.product_id.id == self.production_id.product_id.id:
                        move.cw_qty_done += float_round(cw_quantity, precision_rounding=rounding)
                    elif move.cw_unit_factor:
                        move.cw_qty_done += float_round(cw_quantity * move.cw_unit_factor, precision_rounding=rounding)
                    elif move.unit_factor:
                        move.cw_qty_done += float_round(cw_quantity * move.unit_factor, precision_rounding=rounding)
        produce_move = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel'))
        if produce_move and produce_move.product_id.tracking != 'none':
            existing_move_line = produce_move.move_line_ids.filtered(lambda x: x.lot_id == self.lot_id)
            if existing_move_line:
                existing_move_line.product_cw_uom = self.product_cw_uom_id
                cw_produced_qty = self.product_cw_uom_id._compute_quantity(self.cw_product_qty,
                                                                           existing_move_line.product_cw_uom)
                existing_move_line.product_cw_uom_qty += cw_produced_qty
                existing_move_line.cw_qty_done += cw_produced_qty
        return res

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProductProduce, self)._onchange_product_qty()
        super(MrpProductProduce, self)._onchange_product_qty()
        qty_todo = self.product_uom_id._compute_quantity(self.product_qty, self.production_id.product_uom_id,
                                                         round=False)
        if self.product_id._is_cw_product():
            factor = self.production_id.product_uom_id._compute_quantity(self.product_qty,
                                                                         self.production_id.bom_id.product_uom_id) / self.production_id.bom_id.product_qty
            qty = self.production_id.bom_id.cw_product_qty * factor
            self.cw_product_qty = qty
            cw_qty_todo = qty
        else:
            cw_qty_todo = qty_todo
        ml = 0
        for move in self.production_id.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel') and m.bom_line_id):
            qty_to_consume = float_round(qty_todo * move.unit_factor, precision_rounding=move.product_uom.rounding)
            cw_qty_to_consume = float_round(cw_qty_todo * move.cw_unit_factor,
                                            precision_rounding=move.product_cw_uom.rounding)
            produce_lines = self.produce_line_ids.filtered(lambda l: l.move_id == move)
            line = 0
            for produce_line in produce_lines:
                move_line = move.move_line_ids
                if produce_line.lot_id:
                    move_line = move_line.filtered(lambda l: l.lot_id == produce_line.lot_id)
                if move.needs_lots and not produce_line.lot_id and len(move_line) > 1:
                    move_line = move_line[line]
                if float_compare(qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) <= 0:
                    break
                if move_line.lot_produced_id or float_compare(move_line.product_uom_qty,
                                                              move_line.qty_done,
                                                              precision_rounding=move.product_uom.rounding) <= 0:
                    continue
                cw_to_consume_in_line = min(cw_qty_to_consume, move_line.product_cw_uom_qty)
                produce_line.cw_qty_to_consume = cw_to_consume_in_line
                produce_line.cw_qty_done = cw_to_consume_in_line
                produce_line.cw_qty_reserved = min(cw_to_consume_in_line, move_line.product_cw_uom_qty)
                produce_line.product_cw_uom_id = move.product_cw_uom.id
                if float_compare(cw_qty_to_consume, 0.0, precision_rounding=move.product_uom.rounding) > 0 and (not \
                move_line[line] or not move_line[line].lot_id):
                    if move.product_id.tracking == 'serial':
                        cw_qty_to_consume = float_round(cw_qty_todo * move.cw_unit_factor,
                                                        precision_rounding=move.product_cw_uom.rounding) / qty_to_consume
                        produce_line.cw_qty_to_consume = cw_qty_to_consume
                        produce_line.cw_qty_done = cw_qty_to_consume
                        produce_line.product_cw_uom_id = move.product_cw_uom.id
                    else:
                        produce_line.cw_qty_to_consume = cw_qty_to_consume
                        produce_line.cw_qty_done = cw_qty_to_consume
                        produce_line.product_cw_uom_id = move.product_cw_uom.id



class MrpProductProduceLine(models.TransientModel):
    _inherit = "mrp.product.produce.line"

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    cw_qty_to_consume = fields.Float('CW To Consume', digits=dp.get_precision('Product Unit of Measure'))
    product_cw_uom_id = fields.Many2one('uom.uom', 'CW Unit of Measure')
    cw_qty_done = fields.Float('CW Consumed', digits=dp.get_precision('Product Unit of Measure'))
    cw_qty_reserved = fields.Float('CW Reserved', digits=dp.get_precision('Product Unit of Measure'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(MrpProductProduceLine, self)._onchange_product_id()
        self.product_cw_uom_id = self.product_id.cw_uom_id.id
