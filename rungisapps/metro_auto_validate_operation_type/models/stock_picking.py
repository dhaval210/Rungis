from odoo import _, api, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_auto_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))

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
                        raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
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

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
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
            context = self._context
            backorder_confirm = self.env['stock.backorder.confirmation'].create(
                {'pick_ids': [(4, p.id) for p in self]})
            if context.get('cancel_backorder', False) is True:
                backorder_confirm.process_cancel_backorder()
            else:
                backorder_confirm.process()
        self.action_done()
        return

    @api.multi
    def _check_entire_pack(self):
        # get filter domain from configuration
        params = self.env['ir.config_parameter'].sudo()
        auto_validate = params.get_param(
            'metro_auto_validate_operation_type.auto_validate_picking'
        )
        filter_id = params.get_param(
            'metro_auto_validate_operation_type.assign_picking_filter_id'
        )
        filter_domain = self.env['ir.filters'].search([
            ('id', '=', filter_id)]
        )._get_eval_domain()

        # check if there is still an open record
        model_rec_id = self.search(filter_domain)
        """ This function check if entire packs are moved in the picking"""
        # based on temp dependency should be removed in the future
        if auto_validate == 'True':
            for picking in self:
                has_checks = picking._compute_inspection()
                if (
                    picking.id is not False and
                    picking.id in model_rec_id.ids and
                    has_checks is False
                ):
                    origin_packages = picking.move_line_ids.mapped("package_id")
                    for pack in origin_packages:
                        if picking._check_move_lines_map_quant_package(pack):
                            package_level_ids = picking.package_level_ids.filtered(lambda pl: pl.package_id == pack)
                            move_lines_to_pack = picking.move_line_ids.filtered(lambda ml: ml.package_id == pack)
                            if not package_level_ids:
                                spl = self.env['stock.package_level'].create({
                                    'picking_id': picking.id,
                                    'package_id': pack.id,
                                    'location_id': pack.location_id.id,
                                    'location_dest_id': picking.move_line_ids.filtered(lambda ml: ml.package_id == pack).mapped('location_dest_id')[:1].id,
                                    'move_line_ids': [(6, 0, move_lines_to_pack.ids)],
                                })
                                pack_data = {'result_package_id': pack.id}

                                move_lines_to_pack.write(pack_data)
                                spl.write({
                                    'is_done': True,
                                    'is_fresh_package': False,
                                })
                            else:
                                move_lines_in_package_level = move_lines_to_pack.filtered(lambda ml: ml.move_id.package_level_id)
                                move_lines_without_package_level = move_lines_to_pack - move_lines_in_package_level
                                for ml in move_lines_in_package_level:
                                    ml.write({
                                        'result_package_id': pack.id,
                                        'package_level_id': ml.move_id.package_level_id.id,
                                    })
                                move_lines_without_package_level.write({
                                    'result_package_id': pack.id,
                                    'package_level_id': package_level_ids[0].id,
                                })
                    picking.button_auto_validate()
                else:
                    super()._check_entire_pack()
        else:
            super()._check_entire_pack()
