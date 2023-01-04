# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    product_cw_uom_id = fields.Many2one('uom.uom', 'CW Unit of Measure', readonly=True,
                                        help='Technical: used in views only.')
    cw_qty_production = fields.Float('Original Production Quantity', readonly=True,
                                     related='production_id.cw_product_qty')
    cw_qty_remaining = fields.Float('CW Quantity To Be Produced',
                                    digits=dp.get_precision('Product CW Unit of Measure'))
    cw_qty_produced = fields.Float(
        'CW Quantity', default=0.0,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="Total CW Quantity already handled by this work order")
    cw_qty_producing = fields.Float(
        'Currently Produced CW Quantity', default=0.0,
        digits=dp.get_precision('Product CW Unit of Measure'),
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    cw_is_produced = fields.Boolean(string="Has Been Produced(CW)",
                                    compute='_cw_compute_is_produced')

    @api.one
    @api.depends('production_id.cw_product_qty', 'cw_qty_produced')
    def _cw_compute_is_produced(self):
        rounding = self.production_id.product_cw_uom_id.rounding
        self.cw_is_produced = float_compare(self.cw_qty_produced, self.production_id.cw_product_qty,
                                            precision_rounding=rounding) >= 0

    @api.multi
    @api.depends('cw_qty_production', 'cw_qty_produced')
    def _compute_cw_qty_remaining(self):
        for wo in self:
            wo.cw_qty_remaining = float_round(wo.cw_qty_production - wo.cw_qty_produced,
                                              precision_rounding=wo.production_id.product_cw_uom_id.rounding)

    def _get_byproduct_move_line(self, by_product_move, quantity):
        res = super(MrpWorkorder, self)._get_byproduct_move_line(by_product_move, quantity)
        if by_product_move.product_id._is_cw_product():
            if by_product_move.has_tracking == 'serial':
                cw_quantity = by_product_move.product_cw_uom._compute_quantity(
                    self.qty_producing * by_product_move.cw_unit_factor, by_product_move.product_id.cw_uom_id)
            else:
                cw_quantity = self.cw_qty_producing * by_product_move.cw_unit_factor
            res.update({
                'product_cw_uom_qty': cw_quantity,
                'product_cw_uom': by_product_move.product_cw_uom.id,
                'cw_qty_done': cw_quantity,
            })
        return res

    def _generate_lot_ids(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpWorkorder, self)._generate_lot_ids()
        cw_params = self._context.get('cw_params')
        rounding = self.production_id.product_cw_uom_id.rounding
        if cw_params and 'generate_lot_ids_qty' in cw_params:
            self.cw_qty_producing = cw_params.get('generate_lot_ids_qty')
            cw_params.pop('generate_lot_ids_qty', None)
        else:
            if float_compare(self.cw_qty_produced, self.production_id.cw_product_qty, precision_rounding=rounding) >= 0:
                self.cw_qty_producing = 0
            elif self.production_id.product_id.tracking == 'serial':
                self.cw_qty_producing = float_round(self.production_id.cw_product_qty - self.cw_qty_produced,
                                                    precision_rounding=rounding)
                self.cw_qty_producing = self.cw_qty_producing /self.qty_production
            else:
                self.cw_qty_producing = float_round(self.production_id.cw_product_qty - self.cw_qty_produced,
                                                    precision_rounding=rounding)
        self.ensure_one()
        MoveLine = self.env['stock.move.line']
        tracked_moves = self.move_raw_ids.filtered(
            lambda move: move.state not in ('done',
                                            'cancel') and move.product_id.tracking != 'none' and move.product_id != self.production_id.product_id and move.bom_line_id)
        for move in tracked_moves:
            qty = move.unit_factor * self.qty_producing
            cw_qty = move.cw_unit_factor * self.cw_qty_producing
            cw_qty_serial = cw_qty / qty
            if move.product_id.tracking == 'serial':
                while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                    MoveLine.create({
                        'move_id': move.id,
                        'product_uom_qty': 0,
                        'product_cw_uom_qty': 0,
                        'product_uom_id': move.product_uom.id,
                        'product_cw_uom': move.product_cw_uom.id,
                        'qty_done': min(1, qty),
                        'cw_qty_done': cw_qty_serial,
                        'production_id': self.production_id.id,
                        'workorder_id': self.id,
                        'product_id': move.product_id.id,
                        'done_wo': False,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
                    qty -= 1
            else:
                MoveLine.create({
                    'move_id': move.id,
                    'product_uom_qty': 0,
                    'product_cw_uom_qty': 0,
                    'product_uom_id': move.product_uom.id,
                    'product_cw_uom': move.product_cw_uom.id,
                    'qty_done': qty,
                    'cw_qty_done': cw_qty,
                    'product_id': move.product_id.id,
                    'production_id': self.production_id.id,
                    'workorder_id': self.id,
                    'done_wo': False,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })

    @api.multi
    def record_production(self):
        lot_id = self.final_lot_id
        if not self:
            return True
        context = self._context.copy()
        if context.get('cw_params'):
            context['cw_params'].update({'flag_button_finish': 0})
        else:
            context['cw_params'] = {'flag_button_finish': 0}
        self.env.context = context
        self.ensure_one()
        if self.product_id._is_cw_product():
            if self.cw_qty_producing <= 0:
                raise UserError(
                    _('Please set the CW Quantity you are currently producing. It should be different from zero.'))
        mrp_list = []
        for move in self.move_raw_ids:
            if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) and move.bom_line_id \
                    and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
                rounding = move.product_uom.rounding
                cw_rounding = move.product_cw_uom.rounding
                producting_qty = self.cw_qty_producing if self.cw_qty_producing else self.qty_producing
                if self.product_id.tracking != 'none':
                    cw_qty_to_add = float_round(producting_qty * move.cw_unit_factor,
                                                precision_rounding=cw_rounding)
                    mrp_list.append(cw_qty_to_add)
                    context = self._context.copy()
                    if context.get('cw_params'):
                        context['cw_params'].update({'mrp_list': mrp_list})
                    else:
                        context['cw_params'] = {'mrp_list': mrp_list}
                    self.env.context = context
                elif len(move._get_move_lines()) < 2:
                    move.cw_qty_done += float_round(producting_qty * move.cw_unit_factor,
                                                    precision_rounding=rounding)

                else:
                    move._set_cw_quantity_done(
                        move.cw_quantity_done + float_round(producting_qty * move.cw_unit_factor,
                                                            precision_rounding=rounding))
        super(MrpWorkorder, self).record_production()
        context = self._context.copy()
        if context.get('cw_params'):
            context['cw_params'].update({'flag_button_finish': 1})
        else:
            context['cw_params'] = {'flag_button_finish': 1}
        self.env.context = context
        for move_line in self.active_move_line_ids:
            if move_line.product_id.tracking != 'none' and not move_line.lot_id:
                raise UserError(_('You should provide a lot/serial number for a component.'))
            lots = self.move_line_ids.filtered(
                lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (
                        x.product_id == move_line.product_id))
            if lots:
                lots[0].cw_qty_done += move_line.cw_qty_done

        self.move_line_ids.filtered(
            lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.cw_qty_done > 0
        ).write({
            'cw_lot_produced_qty': self.cw_qty_producing
        })
        if not self.next_work_order_id:
            production_move = self.production_id.move_finished_ids.filtered(
                lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
            if production_move.product_id.tracking != 'none':
                move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == lot_id.id)
                if move_line:
                    move_line.product_cw_uom_qty += self.cw_qty_producing
                    move_line.cw_qty_done += self.cw_qty_producing
                    move_line.product_cw_uom = production_move.product_cw_uom.id
            else:
                production_move.cw_qty_done += self.cw_qty_producing
        self.cw_qty_produced += self.cw_qty_producing
        rounding = self.production_id.product_cw_uom_id.rounding
        if float_compare(self.cw_qty_produced, self.production_id.cw_product_qty, precision_rounding=rounding) >= 0:
            self.cw_qty_producing = 0
        rounding = self.production_id.product_uom_id.rounding
        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.button_finish()
        return True

    @api.multi
    def button_finish(self):
        cw_params = self._context.get('cw_params')
        if 'flag_button_finish' in cw_params.keys():
            flag_button_finish = cw_params['flag_button_finish']
            if flag_button_finish == 1:
                return super(MrpWorkorder, self).button_finish()
            elif flag_button_finish == 0:
                return
        else:
            return super(MrpWorkorder, self).button_finish()
