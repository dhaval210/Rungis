# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.multi
    def action_do_produce_generate_lot(self):
        raw_move = self.production_id.move_raw_ids.filtered(lambda m: m.bom_line_id.auto_lot_creation and m.state not in ('done', 'cancel'))
        if raw_move:
            if not self.lot_id:
                move_line_ids = raw_move and raw_move[0].active_move_line_ids
                produce_move = self.production_id.move_finished_ids.filtered(lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel'))
                if produce_move and produce_move.product_id.tracking == 'lot':
                    for move_line in move_line_ids:
                        lot = self.env['stock.production.lot'].search([('name', '=', move_line.lot_id.name), ('product_id', '=', self.product_id.id)])
                        if not lot:
                            lot = move_line.lot_id.copy({'product_id': self.product_id.id})
                            lot.write({
                                'use_date': move_line.lot_id.use_date,
                                'removal_date': move_line.lot_id.removal_date,
                                'life_date': move_line.lot_id.life_date,
                                'alert_date': move_line.lot_id.alert_date,
                            })
                        existing_move_line = produce_move.move_line_ids.filtered(lambda x: x.lot_id == lot)
                        quantity_done = raw_move and float_round((self.product_qty / raw_move[0].product_qty)* move_line.product_qty, precision_rounding=raw_move[0].product_uom.rounding)
                        if not existing_move_line:
                            vals = {
                              'move_id': produce_move.id,
                              'product_id': produce_move.product_id.id,
                              'location_id': produce_move.location_id.id,
                              'location_dest_id': produce_move.location_dest_id.id,
                              'product_uom_id': produce_move.product_uom.id,
                              'production_id': self.production_id.id,
                              'lot_id': lot.id,
                              'qty_done': quantity_done,
                              'product_uom_qty': quantity_done,
                            }
                            self.env['stock.move.line'].create(vals)

                for pl in self.produce_line_ids:
                    if pl.qty_done:
                        if pl.product_id.tracking != 'none' and not pl.lot_id:
                            raise UserError(_('Please enter a lot or serial number for %s !' % pl.product_id.display_name))
                        if not pl.move_id:
                            move_id = self.production_id.move_raw_ids.filtered(lambda m: m.product_id == pl.product_id and m.state not in ('done', 'cancel'))
                            if move_id:
                                pl.move_id = move_id
                            else:
                                order = self.production_id
                                pl.move_id = self.env['stock.move'].create({
                                            'name': order.name,
                                            'product_id': pl.product_id.id,
                                            'product_uom': pl.product_uom_id.id,
                                            'location_id': order.location_src_id.id,
                                            'location_dest_id': self.product_id.property_stock_production.id,
                                            'raw_material_production_id': order.id,
                                            'group_id': order.procurement_group_id.id,
                                            'origin': order.name,
                                            'state': 'confirmed'})
                        pl.move_id.generate_consumed_move_line(pl.qty_done, pl.lot_produced_id, lot=pl.lot_id)
                if self.production_id.state == 'confirmed':
                    self.production_id.write({
                        'state': 'progress',
                        'date_start': datetime.now(),
                    })
                move_line_to_unlink = self.production_id.move_raw_ids.mapped('active_move_line_ids').filtered(lambda ml: not ml.lot_produced_id)
                move_line_to_unlink.unlink()
            else:
                self.do_produce()
        else:
            self.do_produce()

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        super(MrpProductProduce, self)._onchange_product_qty()
        raw_move = self.production_id.move_raw_ids.filtered(lambda m: m.bom_line_id.auto_lot_creation and m.state not in ('done', 'cancel'))
        move_line_ids = raw_move and raw_move[0].active_move_line_ids
        line = 0
        for move_line in move_line_ids:
            lot = self.env['stock.production.lot'].search([('name', '=', move_line.lot_id.name), ('product_id', '=', self.product_id.id)])
            if not lot and move_line.lot_id:
                lot = move_line.lot_id.copy({'product_id': self.product_id.id})
                lot.write({
                    'use_date': move_line.lot_id.use_date,
                    'removal_date': move_line.lot_id.removal_date,
                    'life_date': move_line.lot_id.life_date,
                    'alert_date': move_line.lot_id.alert_date,
                })
            self.produce_line_ids[line].lot_produced_id = lot.id
            line += 1


class MrpProductProduceLine(models.TransientModel):
    _inherit = "mrp.product.produce.line"

    lot_produced_id = fields.Many2one('stock.production.lot', 'Finished Lot/Serial Number')

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        super(MrpProductProduceLine, self)._onchange_lot_id()
        stock_quant = self.product_id.stock_quant_ids.filtered(lambda x: x.lot_id.id == self.lot_id.id and x.product_id.id == self.product_id.id)
        raw_move = self.product_produce_id.production_id.move_raw_ids.filtered(lambda m: m.bom_line_id.auto_lot_creation and m.state not in ('done', 'cancel'))
        move_line_ids = raw_move and raw_move[0].active_move_line_ids
        move_line = move_line_ids.filtered(lambda x: x.lot_id.name == self.lot_produced_id.name and x.move_id.product_id.id == self.product_id.id)
        move_line.write({'lot_id':  self.lot_id.id})
        self.lot_produced_id = self.env['stock.production.lot'].search([('name', '=', self.lot_id.name), ('product_id', '=', self.product_produce_id.production_id.product_id.id)])

