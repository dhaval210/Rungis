# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    cw_product_qty = fields.Float('CW Quantity', default=0.0,digits=dp.get_precision('Product CW Unit of Measure'),
        states={'done': [('readonly', True)]})
    product_cw_uom_id = fields.Many2one(
        'uom.uom', 'CW Unit of Measure',
        states={'done': [('readonly', True)]})

    @api.onchange('mo_id')
    def onchange_mo_id(self):
        super(MrpUnbuild, self).onchange_mo_id()
        if self.mo_id:
            self.cw_product_qty = self.mo_id.cw_product_qty

    @api.onchange('product_id','product_qty')
    def onchange_product_quantity(self):
        if self.product_id:
            self.product_cw_uom_id = self.product_id.cw_uom_id.id
        if self.product_id and self.product_qty and self.bom_id.product_qty:
            factor = self.product_uom_id._compute_quantity(self.product_qty,
                                                               self.bom_id.product_uom_id) / self.bom_id.product_qty
            self.cw_product_qty = self.bom_id.cw_product_qty * factor

    @api.constrains('cw_product_qty')
    def _check_cw_qty(self):
        if self.product_id._is_cw_product():
            if self.product_qty <= 0:
                raise ValueError(_('Unbuild Order product CW Quantity has to be strictly positive.'))

    @api.multi
    def action_unbuild(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpUnbuild, self).action_unbuild()

        self.ensure_one()
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise UserError(_('You should provide a lot number for the final product.'))

        if self.mo_id:
            if self.mo_id.state != 'done':
                raise UserError(_('You cannot unbuild a undone manufacturing order.'))

        consume_move = self._generate_consume_moves()[0]
        produce_moves = self._generate_produce_moves()

        if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
            raise UserError(_(
                'Some of your components are tracked, you have to specify a manufacturing order in order to retrieve the correct components.'))

        if consume_move.has_tracking != 'none':
            self.env['stock.move.line'].create({
                'move_id': consume_move.id,
                'lot_id': self.lot_id.id,
                'qty_done': consume_move.product_uom_qty,
                'cw_qty_done': consume_move.product_cw_uom_qty,
                'product_id': consume_move.product_id.id,
                'product_uom_id': consume_move.product_uom.id,
                'product_cw_uom': consume_move.product_cw_uom.id,
                'location_id': consume_move.location_id.id,
                'location_dest_id': consume_move.location_dest_id.id,
            })
        else:
            consume_move.quantity_done = consume_move.product_uom_qty
            consume_move.cw_qty_done = consume_move.product_cw_uom_qty
        consume_move._action_done()

        for produce_move in produce_moves:

            if produce_move.has_tracking != 'none':
                original_move = self.mo_id.move_raw_ids.filtered(
                    lambda move: move.product_id == produce_move.product_id)
                needed_quantity = produce_move.product_qty
                cw_needed_quantity = produce_move.cw_product_qty
                for move_lines in original_move.mapped('move_line_ids').filtered(
                        lambda ml: ml.lot_produced_id == self.lot_id):
                    taken_quantity = min(needed_quantity, move_lines.qty_done)
                    cw_taken_quantity = min(cw_needed_quantity, move_lines.cw_qty_done)
                    if taken_quantity:
                        self.env['stock.move.line'].create({
                            'move_id': produce_move.id,
                            'lot_id': move_lines.lot_id.id,
                            'qty_done': taken_quantity,
                            'cw_qty_done': cw_taken_quantity,
                            'product_id': produce_move.product_id.id,
                            'product_uom_id': move_lines.product_uom_id.id,
                            'product_cw_uom': move_lines.product_cw_uom.id,
                            'location_id': produce_move.location_id.id,
                            'location_dest_id': produce_move.location_dest_id.id,
                        })
                        needed_quantity -= taken_quantity
                        cw_needed_quantity -= cw_taken_quantity
            else:
                produce_move.cw_qty_done = produce_move.product_cw_uom_qty
                produce_move.quantity_done = produce_move.product_uom_qty
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.qty_done > 0)
        consume_move.move_line_ids.write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        return self.write({'state': 'done'})

    def _generate_consume_moves(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpUnbuild, self)._generate_consume_moves()
        moves = self.env['stock.move']
        for unbuild in self:
            move = self.env['stock.move'].create({
                'name': unbuild.name,
                'date': unbuild.create_date,
                'product_id': unbuild.product_id.id,
                'product_uom': unbuild.product_uom_id.id,
                'product_uom_qty': unbuild.product_qty,
                'product_cw_uom': unbuild.product_cw_uom_id.id,
                'product_cw_uom_qty': unbuild.cw_product_qty,
                'location_id': unbuild.location_id.id,
                'location_dest_id': unbuild.product_id.property_stock_production.id,
                'warehouse_id': unbuild.location_id.get_warehouse().id,
                'origin': unbuild.name,
                'consume_unbuild_id': unbuild.id,
            })
            move._action_confirm()
            moves += move
        return moves

    def _generate_produce_moves(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpUnbuild, self)._generate_produce_moves()
        moves = self.env['stock.move']
        for unbuild in self:
            if unbuild.mo_id:
                raw_moves = unbuild.mo_id.move_raw_ids.filtered(lambda move: move.state == 'done')
                factor = unbuild.product_qty / unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.product_qty,
                                                                                              unbuild.product_uom_id)
                for raw_move in raw_moves:
                    moves += unbuild._generate_move_from_raw_moves(raw_move, factor)
            else:
                factor = unbuild.product_uom_id._compute_quantity(unbuild.product_qty,
                                                                  unbuild.bom_id.product_uom_id) / unbuild.bom_id.product_qty
                boms, lines = unbuild.bom_id.explode(unbuild.product_id, factor,
                                                     picking_type=unbuild.bom_id.picking_type_id)
                for line, line_data in lines:
                    move = unbuild._generate_move_from_bom_line(line, line_data['qty'])
                    move.write({
                        'product_cw_uom_qty': line_data['cw_qty'],
                        'product_cw_uom': line.product_uom_id.id,
                    })
                    moves += move
        return moves

    def _generate_move_from_raw_moves(self, raw_move, factor):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpUnbuild, self)._generate_move_from_raw_moves(raw_move, factor)
        res = super(MrpUnbuild, self)._generate_move_from_raw_moves(raw_move, factor)
        res.write({
            'product_cw_uom_qty': raw_move.product_cw_uom_qty * factor,
            'product_cw_uom': raw_move.product_cw_uom.id,
        })
        return res

