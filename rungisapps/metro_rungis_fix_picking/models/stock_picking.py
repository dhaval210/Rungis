from odoo import models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def check_fix_move_lines(self):
        fixed_lines = 0
        for ml in self.move_line_ids:
            if ml.product_cw_uom_qty == 0 and ml.cw_qty_done > 0:
                ml.with_context(bypass_reservation_update=True).write({'product_cw_uom_qty': ml.cw_qty_done})            
            quant = self.env['stock.quant'].search([
                ('product_id', '=', ml.product_id.id if ml.product_id else False),
                ('location_id', '=', ml.location_id.id if ml.location_id else False),
                ('package_id', '=', ml.package_id.id if ml.package_id else False),
                ('lot_id', '=', ml.lot_id.id if ml.lot_id else False),
            ], limit=1)
            all_move_line = self.env['stock.move.line'].search([
                ('product_id', '=', ml.product_id.id if ml.product_id else False),
                ('location_id', '=', ml.location_id.id if ml.location_id else False),
                ('package_id', '=', ml.package_id.id if ml.package_id else False),
                ('lot_id', '=', ml.lot_id.id if ml.lot_id else False),
            ])
            new_cw_stock_reserved_quantity = sum(all_move_line.mapped('product_cw_uom_qty'))
            new_reserved_quantity = sum(all_move_line.mapped('product_uom_qty'))
            if not quant or quant.id is False:
                data = {
                    'cw_stock_reserved_quantity': new_cw_stock_reserved_quantity,
                    'reserved_quantity': new_reserved_quantity,
                    'cw_stock_quantity': new_cw_stock_reserved_quantity,
                    'quantity': new_reserved_quantity,
                    'lot_id': ml.lot_id.id if ml.lot_id else False,
                    'package_id': ml.package_id.id if ml.package_id else False,
                    'location_id': ml.location_id.id if ml.location_id else False,
                    'product_id': ml.product_id.id if ml.product_id else False,
                }
                quant = self.env['stock.quant'].sudo().create(data)
                fixed_lines += 1
            if quant:
                if quant.cw_stock_reserved_quantity == new_cw_stock_reserved_quantity and quant.reserved_quantity == new_reserved_quantity:
                    continue
                data = {
                    'cw_stock_reserved_quantity': new_cw_stock_reserved_quantity,
                    'reserved_quantity': new_reserved_quantity,
                }

                if quant.cw_stock_quantity < new_cw_stock_reserved_quantity:
                    data.update({'cw_stock_quantity': new_cw_stock_reserved_quantity})
                if quant.quantity < new_reserved_quantity:
                    data.update({'quantity': new_reserved_quantity})

                quant.sudo().write(data)
                fixed_lines += 1

        message_id = self.env['message.wiz'].create({
            'message': _(str(fixed_lines) + ' move lines were fixed by the job')
        })
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wiz',
            'res_id': message_id.id,
            'target': 'new'
        }
