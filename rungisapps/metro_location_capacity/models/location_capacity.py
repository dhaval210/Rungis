# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockLocation(models.Model):
    _inherit = "stock.location"

    location_capacity = fields.Float(string='Capacity', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    @api.multi
    def _get_remaining_capacity(self, product_id):
        location_capacity = self.location_capacity
        quant_obj = self.env['stock.quant']
        onhand_qty = quant_obj._get_available_quantity(
            product_id, self)
        qty_res = quant_obj._gather(product_id,
                                    self)
        reserved_qty = sum(qty_res.mapped('reserved_quantity'))
        remaining_capacity = location_capacity - (onhand_qty + reserved_qty)
        return remaining_capacity


class StockMove(models.Model):
    _inherit = "stock.move"

    no_availability = fields.Boolean()

    def action_show_details(self):
        if self.state not in ['done', 'cancel']:
            for line in self.move_line_ids:
                availability = self._check_location_availability(
                    self.product_uom_qty)
                self.no_availability = True if not availability else False
        return super(StockMove, self).action_show_details()

    def _check_location_availability(self, qty):
        picking_id = self.picking_id
        # move_id = self.move_id
        self.move_line_ids.unlink()
        move_line = self.move_line_ids
        # for move in move_line:
        putaway_strategy_id = picking_id.location_dest_id.putaway_strategy_id
        total_done = 0
        if move_line:
            for line in move_line:
                # total_done += line.qty_done
                remaining_capacity = \
                    line.location_dest_id._get_remaining_capacity(
                        self.product_id)
                if remaining_capacity and remaining_capacity >= qty:
                    line.update({'product_uom_qty': qty,
                                 # 'qty_done': qty
                                 })
                    qty -= qty
                elif remaining_capacity and remaining_capacity < qty:
                    line.update({'product_uom_qty': remaining_capacity,
                                 'qty_done': remaining_capacity
                                 })
                    qty -= remaining_capacity
                elif remaining_capacity == 0:
                    line.unlink()

        if putaway_strategy_id and total_done < self.product_uom_qty:
            child_ids = putaway_strategy_id.product_location_ids
            for child in child_ids:
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
            if qty != 0:
                raise UserError(_("No location to store remaining qty"))
        return

    class StockLocation(models.Model):
        _inherit = "stock.picking"

        @api.multi
        def button_validate(self):
            self.ensure_one()
            if not self.move_lines and not self.move_line_ids:
                raise UserError(_('Please add some items to move.'))

            # If no lots when needed, raise error
            picking_type = self.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done,
                                                   precision_digits=precision_digits)
                                     for move_line in
                                     self.move_line_ids.filtered(
                                         lambda m: m.state not in (
                                             'done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty,
                                                       precision_rounding=move_line.product_uom_id.rounding)
                                         for move_line in self.move_line_ids)

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = self.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(
                        lambda line: float_compare(line.qty_done, 0,
                                                   precision_rounding=line.product_uom_id.rounding)
                    )

                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            raise UserError(_(
                                'You need to supply a Lot/Serial number for product %s.') % product.display_name)

            if no_quantities_done:
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create(
                    {'pick_ids': [(4, self.id)]})
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            if self._get_overprocessed_stock_moves() and not self._context.get(
                    'skip_overprocessed_check'):
                view = self.env.ref('stock.view_overprocessed_transfer')
                wiz = self.env['stock.overprocessed.transfer'].create(
                    {'picking_id': self.id})
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.overprocessed.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if self._check_backorder():
                return self.action_generate_backorder_wizard()
            self.action_done()
            return
