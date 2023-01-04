# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            if move_line.product_id._is_cw_product():
                if move_line.qty_done != 0 and move_line.cw_qty_done == 0:
                    raise UserError(_("Enter the CW Done quantity for the product %r.") % (move_line.product_id.name))
                elif move_line.qty_done == 0 and move_line.cw_qty_done != 0:
                    raise UserError(_("Enter the Done quantity for the product %r.") % (move_line.product_id.name))
            else:
                move_line.cw_qty_done = 0
                return super(Picking, self).button_validate()
        return super(Picking, self).button_validate()

    def _put_in_pack(self):
        package = False
        for pick in self.filtered(lambda p: p.state not in ('done', 'cancel')):
            move_line_ids = pick.move_line_ids.filtered(lambda o: o.qty_done > 0 and not o.result_package_id)
            if move_line_ids:
                move_lines_to_pack = self.env['stock.move.line']
                package = self.env['stock.quant.package'].create({})
                for ml in move_line_ids:
                    if float_compare(ml.qty_done, ml.product_uom_qty,
                                     precision_rounding=ml.product_uom_id.rounding) >= 0:
                        move_lines_to_pack |= ml
                    else:
                        quantity_left_todo = float_round(
                            ml.product_uom_qty - ml.qty_done,
                            precision_rounding=ml.product_uom_id.rounding,
                            rounding_method='UP')
                        quantity_cw_left_todo = float_round(
                            ml.product_cw_uom_qty - ml.cw_qty_done,
                            precision_rounding=ml.product_cw_uom.rounding,
                            rounding_method='UP')
                        done_to_keep = ml.qty_done
                        done_cw_to_keep = ml.cw_qty_done
                        new_move_line = ml.copy(
                            default={
                                'product_uom_qty': 0,
                                'qty_done': ml.qty_done,
                                'product_cw_uom_qty': 0,
                                'cw_qty_done': ml.cw_qty_done
                            }
                        )
                        ml.write({
                            'product_uom_qty': quantity_left_todo,
                            'qty_done': 0.0,
                            'product_cw_uom_qty': quantity_cw_left_todo,
                            'cw_qty_done': 0.0,
                        })
                        new_move_line.write({
                            'product_uom_qty': done_to_keep,
                            'product_cw_uom_qty': done_cw_to_keep,                          
                        })
                        move_lines_to_pack |= new_move_line

                package_level = self.env['stock.package_level'].create({
                    'package_id': package.id,
                    'picking_id': pick.id,
                    'location_id': False,
                    'location_dest_id': move_line_ids.mapped('location_dest_id').id,
                    'move_line_ids': [(6, 0, move_lines_to_pack.ids)]
                })
                move_lines_to_pack.write({
                    'result_package_id': package.id,
                })
            else:
                raise UserError(_('You must first set the quantity you will put in the pack.'))
        return package

    def put_in_pack(self):
        res = self.check_destinations()
        if res.get('type'):
            return res
        return self._put_in_pack()
