# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    cw_quantity = fields.Float("CW Quantity", digits=dp.get_precision('Product CW Unit of Measure'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-UOM')
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError(_("You may only return one picking at a time."))
        res = super(ReturnPicking, self).default_get(fields)
        move_dest_exists = False
        product_return_moves = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only return Done pickings."))
            for move in picking.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                quantity = move.product_qty - sum(
                    move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']). \
                        mapped('move_line_ids').mapped('product_qty'))
                quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                cw_quantity = move.product_cw_uom_qty - sum(
                    move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']). \
                        mapped('move_line_ids').mapped('product_cw_uom_qty'))
                cw_quantity = float_round(cw_quantity, precision_rounding=move.product_cw_uom.rounding)
                cw_uom = move.product_id.cw_uom_id.id if move.product_id._is_cw_product() else False
                catch_weight_ok = True if move.product_id._is_cw_product() else False
                product_return_moves.append(
                    (0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'cw_quantity': cw_quantity,
                            'move_id': move.id, 'uom_id': move.product_id.uom_id.id,
                            'cw_uom_id': cw_uom, 'catch_weight_ok': catch_weight_ok}))
            if not product_return_moves:
                raise UserError(
                    _("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                res.update({
                    'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': picking.location_id.id})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res

    def _prepare_move_default_values(self, return_line, new_picking):
        res = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        if return_line.product_id._is_cw_product():
            res.update({
                'product_cw_uom_qty': return_line.cw_quantity,
                'product_cw_uom': return_line.product_id.cw_uom_id.id,
            })
        return res
