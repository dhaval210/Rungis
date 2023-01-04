# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'

    cw_unit_factor = fields.Float('Unit Factor')

    def _generate_consumed_move_line(self, qty_to_add, final_lot, lot=False):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._generate_consumed_move_line(qty_to_add, final_lot, lot)
        cw_params = self._context.get('cw_params')
        if cw_params:
            if 'mrp_list' in cw_params:
                quantity_list = cw_params.get('mrp_list')
                cw_qty_to_add = quantity_list[0]
                quantity_list.pop(0)
        if lot:
            move_lines = self.move_line_ids.filtered(lambda ml: ml.lot_id == lot and not ml.lot_produced_id)
        else:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_produced_id)

        if lot and self.product_id.tracking == 'serial' and lot in self.move_line_ids.filtered(
                lambda ml: ml.qty_done).mapped('lot_id'):
            raise UserError(
                _('You cannot consume the same serial number twice. Please correct the serial numbers encoded.'))
        cw_qty = cw_qty_to_add
        for ml in move_lines:
            rounding = ml.product_uom_id.rounding
            if float_compare(qty_to_add, 0, precision_rounding=rounding) <= 0:
                break
            quantity_to_process = min(qty_to_add, ml.product_uom_qty - ml.qty_done)
            cw_quantity_to_process = min(cw_qty_to_add, ml.product_cw_uom_qty - ml.cw_qty_done)
            qty_to_add -= quantity_to_process
            cw_qty_to_add -= cw_quantity_to_process

            new_quantity_done = (ml.qty_done + quantity_to_process)
            cw_new_quantity_done = (ml.cw_qty_done + cw_quantity_to_process)
            if float_compare(new_quantity_done, ml.product_uom_qty, precision_rounding=rounding) >= 0:
                ml.write({'qty_done': new_quantity_done, 'cw_qty_done': cw_new_quantity_done,
                          'lot_produced_id': final_lot.id})
            else:
                new_qty_reserved = ml.product_uom_qty - new_quantity_done
                cw_new_qty_reserved = ml.product_cw_uom_qty - cw_new_quantity_done
                default = {'product_uom_qty': new_quantity_done, 'product_cw_uom_qty': cw_new_quantity_done,
                           'qty_done': new_quantity_done, 'cw_qty_done': cw_new_quantity_done,
                           'lot_produced_id': final_lot.id}
                ml.copy(default=default)
                ml.with_context(bypass_reservation_update=True).write(
                    {'product_uom_qty': new_qty_reserved, 'product_cw_uom_qty': cw_new_qty_reserved, 'qty_done': 0})
            if float_compare(qty_to_add, 0, precision_rounding=self.product_uom.rounding) == 0 and \
                    float_compare(cw_qty_to_add, 0, precision_rounding=self.product_cw_uom.rounding) > 0:
                ml.cw_qty_done = cw_qty

        if float_compare(qty_to_add, 0, precision_rounding=self.product_uom.rounding) > 0:
            quants = self.env['stock.quant']._gather(self.product_id, self.location_id, lot_id=lot, strict=False)
            available_quantity = self.product_id.uom_id._compute_quantity(
                self.env['stock.quant']._get_available_quantity(
                    self.product_id, self.location_id, lot_id=lot, strict=False
                ), self.product_uom
            )

            if self.product_id._is_cw_product():
                cw_available_quantity = self.product_id.cw_uom_id._compute_quantity(
                    self.env['stock.quant']._get_available_cw_quantity(
                        self.product_id, self.location_id, lot_id=lot, strict=False
                    ), self.product_cw_uom
                )
            location_id = False
            if float_compare(qty_to_add, available_quantity, precision_rounding=self.product_uom.rounding) < 0:
                location_id = quants.filtered(lambda r: r.quantity > 0)[-1:].location_id

            vals = {
                'move_id': self.id,
                'product_id': self.product_id.id,
                'location_id': location_id.id if location_id else self.location_id.id,
                'production_id': self.raw_material_production_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_uom_qty': 0,
                'product_cw_uom_qty': 0,
                'product_uom_id': self.product_uom.id,
                'product_cw_uom': self.product_cw_uom.id if self.product_id._is_cw_product() else None,
                'qty_done': qty_to_add,
                'cw_qty_done': cw_qty_to_add,
                'lot_produced_id': final_lot.id,
            }
            if lot:
                vals.update({'lot_id': lot.id})
            self.env['stock.move.line'].create(vals)

    def _set_cw_quantity_done(self, qty):
        for ml in self.move_line_ids:
            ml_qty = ml.product_cw_uom_qty - ml.cw_qty_done
            if ml.product_cw_uom != self.product_cw_uom:
                ml_qty = ml.product_cw_uom._compute_quantity(ml_qty, self.product_cw_uom, round=False)

            taken_qty = min(qty, ml_qty)
            if ml.product_cw_uom_id != self.product_cw_uom:
                taken_qty = self.product_cw_uom._compute_quantity(ml_qty, ml.product_cw_uom, round=False)
            taken_qty = float_round(taken_qty, precision_rounding=ml.product_cw_uom.rounding)
            ml.cw_qty_done += taken_qty
            if ml.product_cw_uom != self.product_cw_uom:
                taken_qty = ml.product_cw_uom._compute_quantity(ml_qty, self.product_cw_uom, round=False)
            qty -= taken_qty

            if float_compare(qty, 0.0, precision_rounding=self.product_cw_uom.rounding) <= 0:
                break
        if float_compare(qty, 0.0, precision_rounding=self.product_cw_uom.rounding) > 0:
            vals = self._prepare_move_line_vals(quantity=0)
            vals['cw_qty_done'] = qty
            ml = self.env['stock.move.line'].create(vals)

    def _decrease_reserved_quanity(self, quantity):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._decrease_reserved_quanity(quantity)
        cw_params = self._context.get('cw_params')
        cw_quantity = 0
        if cw_params and 'decrease_reserved_qty' in cw_params:
            cw_quantity = cw_params.get('decrease_reserved_qty')
            if not cw_quantity:
                return super(StockMove, self)._decrease_reserved_quanity(quantity)
        move_line_to_unlink = self.env['stock.move.line']
        for move in self:
            cw_reserved_quantity = cw_quantity
            reserved_quantity = quantity
            for move_line in move.move_line_ids:
                if move_line.product_uom_qty > reserved_quantity:
                    move_line.write({'product_uom_qty': reserved_quantity,
                                     'product_cw_uom_qty': cw_reserved_quantity})
                else:
                    move_line.write({'product_uom_qty': 0,
                                     'product_cw_uom_qty': 0})
                    reserved_quantity -= move_line.product_uom_qty
                    cw_reserved_quantity -= move_line.product_cw_uom_qty
                if not move_line.product_uom_qty and not move_line.qty_done:
                    move_line_to_unlink |= move_line
        move_line_to_unlink.unlink()
        return True


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    cw_lot_produced_qty = fields.Float(
        ' CW Quantity Finished Product', digits=dp.get_precision('Product CW Unit of Measure'),
        help="Informative, not used in matching")
