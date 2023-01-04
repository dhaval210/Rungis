# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_show_details(self):
        if self.picking_type_id.code == 'incoming':
            if self.state not in ['done', 'cancel']:
                self._check_location_availability(self.product_uom_qty)
            return super(StockMove, self).action_show_details()
        else:
            return super(StockMove, self).action_show_details()

    def _check_location_availability(self, qty):
        picking_id = self.picking_id
        putaway_strategy_id = picking_id.location_dest_id.putaway_strategy_id
        if putaway_strategy_id.product_turnover or \
                putaway_strategy_id.storage_location:
            self.move_line_ids.unlink()
            move_line = self.move_line_ids
            total_done = 0

            if putaway_strategy_id and total_done < self.product_uom_qty:
                child_ids = putaway_strategy_id.product_location_ids
                category_id = putaway_strategy_id.fixed_location_ids
                for child in child_ids:
                    if child.product_id == self.product_id:
                        if child.fixed_location_id.location_capacity > 0:
                            remaining_capacity = child.fixed_location_id._get_remaining_capacity(
                                child.product_id)
                            if qty and qty >= remaining_capacity:
                                qty_to_create = remaining_capacity
                                qty -= remaining_capacity
                            else:
                                qty_to_create = qty
                                qty -= qty
                            if qty_to_create:
                                move_line.create({
                                    'location_dest_id': child.fixed_location_id.id,
                                    'qty_done': qty_to_create,
                                    'move_id': self.id,
                                    'product_id': self.product_id.id,
                                    'product_uom_id': self.product_id.uom_id.id,
                                    'product_uom_qty': qty_to_create,
                                    'location_id': self.location_id.id,
                                })
                    self.state = 'assigned'
                if qty != 0:
                    for categ in category_id:
                        if categ.category_id.id == self.product_id.categ_id.id:
                            if categ.fixed_location_id.location_capacity > 0:
                                remaining_capacity = categ.fixed_location_id._get_remaining_capacity(
                                    categ.product_id)
                                if qty and qty >= remaining_capacity:
                                    qty_to_create = remaining_capacity
                                    qty -= remaining_capacity
                                else:
                                    qty_to_create = qty
                                    qty -= qty
                                if qty_to_create:
                                    move_line.create({
                                        'location_dest_id': categ.fixed_location_id.id,
                                        'qty_done': qty_to_create,
                                        'move_id': self.id,
                                        'product_id': self.product_id.id,
                                        'product_uom_id': self.product_id.uom_id.id,
                                        'product_uom_qty': qty_to_create,
                                        'location_id': self.location_id.id,
                                    })

                    self.state = 'assigned'
                if qty > 0:
                    raise UserError(_("No location to store remaining qty"))

        return
