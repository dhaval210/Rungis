from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transport_id = fields.Many2one('transport.unit', 'Transport')
    picking_treated = fields.Boolean('Picking Treated')

    @api.model
    def do_split(self, picking):
        transport_dict = {}
        for move in picking.move_ids_without_package:
            if move.state not in ['done', 'draft']:
                if move.product_id.transport_id:
                    if move.product_id.transport_id.id not in transport_dict:
                        transport_dict[move.product_id.transport_id.id] = []
                    transport_dict[move.product_id.transport_id.id] += [move.id]
                elif move.product_id.categ_id.transport_id:
                    if move.product_id.categ_id.transport_id.id not in transport_dict:
                        transport_dict[move.product_id.categ_id.transport_id.id] = []
                    transport_dict[move.product_id.categ_id.transport_id.id] += [move.id]
                elif move.location_id.transport_id:
                    if move.location_id.transport_id.id not in transport_dict:
                        transport_dict[move.location_id.transport_id.id] = []
                    transport_dict[move.location_id.transport_id.id] += [move.id]
                elif move.warehouse_id.transport_id:
                    if move.warehouse_id.transport_id.id not in transport_dict:
                        transport_dict[move.warehouse_id.transport_id.id] = []
                    transport_dict[move.warehouse_id.transport_id.id] += [move.id]
                else:
                    if not 'no_transport_unit' in transport_dict:
                        transport_dict['no_transport_unit'] = []
                    transport_dict['no_transport_unit'] += [move.id]
        all_transport_unit = False
        if 'no_transport_unit' not in transport_dict:
            all_transport_unit = True
        first_picking_treated = False
        for key in transport_dict:
            new_moves = self.env['stock.move']
            if all_transport_unit and not first_picking_treated:
                picking.write({'transport_id': key})
                first_picking_treated = True
                continue
            if key != 'no_transport_unit':
                for move_id in transport_dict[key]:
                    move = self.env['stock.move'].browse([move_id])
                    qty_split = move.product_uom_qty
                    qty_uom_split = move.product_uom._compute_quantity(
                        qty_split,
                        move.product_id.uom_id,
                        rounding_method='HALF-UP'
                    )
                    new_move_id = move._split(qty_uom_split)
                    move._do_unreserve()
                    move._action_assign()
                    new_moves |= self.env['stock.move'].browse(new_move_id)
            if new_moves:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id,
                    'transport_id': key
                })
                picking.message_post(
                    body=_(
                        'The backorder <a href="#" '
                        'data-oe-model="stock.picking" '
                        'data-oe-id="%d">%s</a> has been created.'
                    ) % (
                             backorder_picking.id,
                             backorder_picking.name
                         )
                )
                new_moves.write({
                    'picking_id': backorder_picking.id,
                })
                new_moves.mapped('move_line_ids').write({
                    'picking_id': backorder_picking.id,
                })
                new_moves._action_assign()
                # Now we do the split
                self.split_by_capacity(backorder_picking)
        self.split_by_capacity(picking)

    @api.model
    def split_by_capacity(self, picking):
        max_weight_capacity = picking.transport_id.max_weight_capacity
        max_volume_capacity = picking.transport_id.max_volume_capacity
        new_moves = self.env['stock.move']
        new_moves2 = self.env['stock.move']
        current_weight = 0
        current_volume = 0
        for move in picking.move_lines:
            qty_keep = 0
            update_measures = False
            if move.state not in ['done', 'draft']:
                if max_weight_capacity:
                    qty_product_uom = move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id)
                    if current_weight + (move.weight or move.product_uom_qty) > max_weight_capacity:
                        base_weight = (move.product_id.base_qty or 1) * (move.product_id.weight or 1)
                        if max_weight_capacity < base_weight:
                            raise ValidationError(
                                'Please make sure that the transport unit of the Picking can hold the base weight for Product:' + move.product_id.name)
                        remaining_weight = max_weight_capacity - current_weight
                        if remaining_weight < base_weight:
                            qty_uom_split = move.product_uom_qty
                            qty_keep = 0
                        else:
                            qty_keep = int(remaining_weight / (move.product_id.weight or 1))
                            qty_split = qty_product_uom - qty_keep
                            qty_uom_split = move.product_id.uom_id._compute_quantity(qty_split, move.product_uom,
                                                                                     rounding_method='HALF-UP')
                            update_measures = True
                        new_move_id = move.with_context(no_confirm =True)._split(qty_uom_split)
                        move._do_unreserve()
                        move._action_assign()
                        new_moves |= self.env['stock.move'].browse(new_move_id)
                    else:
                        qty_keep = qty_product_uom
                        update_measures = True


                if max_volume_capacity:
                    qty_product_uom = move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id)
                    move_volume = (move.product_id.volume or 1) * qty_product_uom
                    if move_volume and (current_volume + move_volume > max_volume_capacity):
                        base_volume = (move.product_id.base_qty or 1) * (move.product_id.volume or 1)
                        if max_volume_capacity < base_volume:
                            raise ValidationError(
                                'Please make sure that the Transport unit of the Picking can hold the base volume for Product: ' + move.product_id.name)
                        remaining_volume = max_volume_capacity - current_volume
                        if remaining_volume < base_volume:
                            qty_uom_split = move.product_uom_qty
                            qty_keep = 0

                        else:
                            qty_keep = int(remaining_volume / (move.product_id.volume or 1))
                            qty_split = qty_product_uom - qty_keep
                            qty_uom_split = move.product_id.uom_id._compute_quantity(qty_split, move.product_uom, rounding_method='HALF-UP')
                            update_measures = True

                        new_move_id = move.with_context(no_confirm = True)._split(qty_uom_split)
                        move._do_unreserve()
                        move._action_assign()
                        new_moves2 |= self.env['stock.move'].browse(new_move_id)
                    else:
                        qty_keep = qty_product_uom
                        update_measures = True
                if update_measures:
                    current_weight += (move.product_id.weight * qty_keep)
                    current_volume += (move.product_id.volume * qty_keep)
        new_moves = new_moves + new_moves2
        if new_moves:
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'move_line_ids': [],
                'backorder_id': picking.id,
                'transport_id': picking.transport_id.id
            })
            picking.message_post(
                body=_(
                    'The backorder <a href="#" '
                    'data-oe-model="stock.picking" '
                    'data-oe-id="%d">%s</a> has been created.'
                ) % (
                         backorder_picking.id,
                         backorder_picking.name
                     )
            )
            new_moves.write({
                'picking_id': backorder_picking.id,
            })
            new_moves.mapped('move_line_ids').write({
                'picking_id': backorder_picking.id,
            })
            new_moves._action_assign()
            # Now we do the split
            self.split_by_capacity(backorder_picking)
