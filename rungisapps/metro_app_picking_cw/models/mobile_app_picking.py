from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class AppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def _export_move_line(self, line, custom_fields):
        res = super()._export_move_line(line, custom_fields)
        res.update({
            'product_cw_uom': self._export_uom(line.product_cw_uom),
            'product_cw_uom_qty': line.product_cw_uom_qty,
            'cw_qty_done': line.cw_qty_done,
            'catch_weight_ok': line.catch_weight_ok,
        })
        return res

    @api.model
    def save_new_line(self, params):
        del params['result_package_id']
        location_dest = self._extract_param(params, 'location_dest_id', 0)
        move_line_id = self._extract_param(params, 'id')
        params.update({'move': params})
        # remove before save
        del params['location_dest_id']
        # save line without dest location
        self.save_line(params)
        # duplicate move.line
        StockMoveLine = self.env['stock.move.line']
        move_line = StockMoveLine.search([('id', '=', move_line_id)])
        if move_line.id > 0:
            quantity_left_todo = float_round(
                move_line.product_uom_qty - move_line.qty_done,
                precision_rounding=move_line.product_uom_id.rounding,
                rounding_method='UP')
            quantity_cw_left_todo = float_round(
                move_line.product_cw_uom_qty - move_line.cw_qty_done,
                precision_rounding=move_line.product_cw_uom.rounding,
                rounding_method='UP')
            done_to_keep = move_line.qty_done
            done_cw_to_keep = move_line.cw_qty_done
            # new line with done values
            new_move_line = move_line.copy(
                default={
                    'product_uom_qty': 0,
                    'qty_done': move_line.qty_done,
                    'product_cw_uom_qty': 0,
                    'cw_qty_done': move_line.cw_qty_done
                }
            )
            # update old line with new reserved values
            move_line.write({
                'product_uom_qty': quantity_left_todo,
                'qty_done': 0.0,
                'product_cw_uom_qty': quantity_cw_left_todo,
                'cw_qty_done': 0.0,
                'pack_mhd': False,
                'lot_mhd': False,
                'lot_id': False,
                'lot_name': False,                
            })
            # update new line with new reserved values
            new_move_line.write({
                'product_uom_qty': done_to_keep,
                'product_cw_uom_qty': done_cw_to_keep,
                'location_dest_id': location_dest,
            })
            return new_move_line.id
        return False

    @api.model
    def get_line_params(self, params):
        res = super().get_line_params(params)
        cw_qty_done = self._extract_param(params, 'cw_qty_done', 0)
        res.update({
            'cw_qty_done': cw_qty_done,
        })
        return res
