# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'

    def generate_consumed_move_line(self, qty_to_add, final_lot, lot=False):
        Quant = self.env['stock.quant']
        auto_bom_creation = self.bom_line_id.mapped('auto_lot_creation')
        if lot:
            move_lines = self.move_line_ids.filtered(lambda ml: ml.lot_id == lot and not ml.lot_produced_id)
        else:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_produced_id)
            move_lines.write({'product_uom_qty': 0.0})
            active_lines = move_lines.mapped('production_id').move_raw_ids.mapped('active_move_line_ids').filtered(lambda x: x.lot_id)
            
            if move_lines and auto_bom_creation:
                for line in active_lines:
                    vals = {
                        'move_id': self.id,
                        'product_id': self.product_id.id,
                        'location_id': line.location_id.id,
                        'production_id': line.production_id.id,
                        'location_dest_id': line.location_dest_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom_id': line.product_uom_id.id,
                        'qty_done': line.qty_done,
                        'lot_produced_id': line.lot_produced_id.id,
                    }
                    move_lines |= self.env['stock.move.line'].create(vals)

        # Sanity check: if the product is a serial number and `lot` is already present in the other
        # consumed move lines, raise.
        if lot and self.product_id.tracking == 'serial' and lot in self.move_line_ids.filtered(lambda ml: ml.qty_done).mapped('lot_id'):
            raise UserError(_('You cannot consume the same serial number twice. Please correct the serial numbers encoded.'))

        for ml in move_lines:
            if not ml.lot_id and ml.product_id.type != 'consu':
                Quant._update_reserved_quantity(ml.product_id, ml.location_id, ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
            rounding = ml.product_uom_id.rounding
            if float_compare(qty_to_add, 0, precision_rounding=rounding) <= 0:
                break
            quantity_to_process = min(ml.lot_id and qty_to_add or ml.qty_done, ml.product_uom_qty - ml.qty_done)
            qty_to_add -= quantity_to_process
            new_quantity_done = (ml.qty_done + quantity_to_process)
            if float_compare(new_quantity_done, ml.product_uom_qty, precision_rounding=rounding) >= 0:
                ml.write({'qty_done': new_quantity_done, 'lot_produced_id': ml.lot_id and final_lot.id or ml.lot_produced_id.id})
            else:
                new_qty_reserved = ml.product_uom_qty - new_quantity_done
                default = {'product_uom_qty': new_quantity_done,
                           'qty_done': new_quantity_done,
                           'lot_produced_id': ml.lot_id and final_lot.id or ml.lot_produced_id.id}
                ml.copy(default=default)
                ml.with_context(bypass_reservation_update=True).write({'product_uom_qty': new_qty_reserved, 'qty_done': 0})

        if float_compare(qty_to_add, 0, precision_rounding=self.product_uom.rounding) > 0:
            # Search for a sub-location where the product is available. This might not be perfectly
            # correct if the quantity available is spread in several sub-locations, but at least
            # we should be closer to the reality. Anyway, no reservation is made, so it is still
            # possible to change it afterwards.
            quants = self.env['stock.quant']._gather(self.product_id, self.location_id, lot_id=lot, strict=False)
            available_quantity = self.product_id.uom_id._compute_quantity(
                self.env['stock.quant']._get_available_quantity(
                    self.product_id, self.location_id, lot_id=lot, strict=False
                ), self.product_uom
            ) # consumed move lines, raise.
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
                'product_uom_id': self.product_uom.id,
                'qty_done': qty_to_add,
                'lot_produced_id': final_lot.id,
            }
            if lot:
                vals.update({'lot_id': lot.id})
            self.env['stock.move.line'].create(vals)