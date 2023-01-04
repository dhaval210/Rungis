from odoo.addons.tis_catch_weight.models import catch_weight
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools import float_round, float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.picking_type_code == 'outgoing' and self.sale_id.client_order_ref:
            purchase_id = self.env['purchase.order'].sudo().search([
                ('name', '=', self.sale_id.client_order_ref),
                ('company_id', '=', 4)
            ], limit=1)
            if purchase_id:
                for sale_move_line in self.move_line_ids_without_package:
                    lot_attribute_lines = sale_move_line.lot_id.lot_attribute_line_ids
                    lot_id = self.env['stock.production.lot'].sudo().search(
                        [('name', '=', sale_move_line.lot_id.name),
                         ('company_id', '=',
                          purchase_id.company_id.id),
                         ('product_id', '=', sale_move_line.lot_id.
                          product_id.id)], limit=1)
                    if lot_id and lot_id.purchase_order_ids:
                        lot_id = lot_id.filtered(lambda lot: purchase_id.partner_id.id in lot.purchase_order_ids.mapped('partner_id.id'))
                    if lot_id:
                        lot_id.sudo().write({
                            'lot_attribute_line_ids': [(6, 0, sale_move_line.lot_id.lot_attribute_line_ids.ids)]
                            if sale_move_line.lot_id.lot_attribute_line_ids else []
                        })
                    if not lot_id:
                        lot_id = self.env['stock.production.lot'].sudo().create({
                            'name': sale_move_line.lot_id.name,
                            'product_id': sale_move_line.product_id.id,
                            'use_date': sale_move_line.lot_id.use_date,
                            'removal_date': sale_move_line.lot_id.removal_date,
                            'life_date': sale_move_line.lot_id.life_date,
                            'alert_date': sale_move_line.lot_id.alert_date,
                            'company_id': purchase_id.company_id.id,
                            'lot_attribute_line_ids': [(6, 0, sale_move_line.lot_id.lot_attribute_line_ids.ids)]
                            if sale_move_line.lot_id.lot_attribute_line_ids else []
                        })
                    purchase_move_id = purchase_id.picking_ids[0].move_ids_without_package.filtered(lambda pick: pick.product_id == sale_move_line.product_id)
                    self.env['stock.move.line'].sudo().create({
                        'product_id': sale_move_line.product_id.id,
                        'product_uom_id': sale_move_line.product_uom_id.id,
                        'location_id': purchase_move_id.location_id.id,
                        'location_dest_id': purchase_move_id.location_dest_id.id,
                        'lot_id': lot_id.id,
                        'product_uom_qty': sale_move_line.product_uom_qty,
                        'product_cw_uom_qty': sale_move_line.product_cw_uom_qty,
                        'lot_attribute_line_ids': [(6, 0, lot_attribute_lines.ids)],
                        'lot_name': lot_id.name,
                        'picking_id': purchase_move_id.picking_id.id,
                        'move_id': purchase_move_id.id,
                        'inter_company_line': True
                    })
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    inter_company_line = fields.Boolean('inter company line', default=False)

    def _action_done(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMoveLine, self)._action_done()
        else:
            cw_params = self._context.get('cw_params')
            ml_to_delete = self.env['stock.move.line']
            for ml in self:
                uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding,
                                      rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
                qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                                          defined on the unit of measure "%s". Please change the quantity done or the \
                                                                          rounding precision of your unit of measure.') % (
                        ml.product_id.display_name, ml.product_uom_id.name))
                qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done_float_compared > 0:
                    if ml.product_id.tracking != 'none':
                        picking_type_id = ml.move_id.picking_type_id
                        if picking_type_id:
                            if picking_type_id.use_create_lots:
                                if ml.lot_name and not ml.lot_id:
                                    lot_id = self.env['stock.production.lot'].search([('name', '=', ml.lot_name),
                                                        ('product_id', '=', ml.product_id.id)], limit=1)
                                    if not lot_id:
                                        lot = self.env['stock.production.lot'].create(
                                            {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                        )
                                    else:
                                        lot = lot_id
                                    ml.write({'lot_id': lot.id})
                            elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                                continue
                        elif ml.move_id.inventory_id:
                            continue
                        if not ml.lot_id:
                            raise UserError(_('You need to supply a lot/serial number for %s.') % ml.product_id.name)
                elif qty_done_float_compared < 0:
                    raise UserError(_('No negative quantities allowed'))
                else:
                    ml_to_delete |= ml
            ml_to_delete.unlink()
            done_ml = self.env['stock.move.line']
            for ml in self - ml_to_delete:
                if ml.product_id.type == 'product':
                    Quant = self.env['stock.quant']
                    rounding = ml.product_uom_id.rounding
                    if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty,
                                                                                        precision_rounding=rounding) > 0:
                        extra_qty = ml.qty_done - ml.product_qty
                        ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id,
                                             package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                    if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                        try:
                            # if condition fixes cw reservation bug with non cw products
                            if ml.product_id._is_cw_product():
                                catch_weight.add_to_context(self, {'cw_reserved_quantity': -ml.cw_product_qty})
                            Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty,
                                                            lot_id=ml.lot_id, package_id=ml.package_id,
                                                            owner_id=ml.owner_id, strict=True)
                        except UserError:
                            # if condition fixes cw reservation bug with non cw products
                            if ml.product_id._is_cw_product():
                                catch_weight.add_to_context(self, {'cw_reserved_quantity': -ml.cw_product_qty})
                            Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty,
                                                            lot_id=False,
                                                            package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                                   rounding_method='HALF-UP')
                    cw_quantity = ml.product_cw_uom._compute_quantity(ml.cw_qty_done, ml.move_id.product_id.cw_uom_id,
                                                                      rounding_method='HALF-UP')
                    catch_weight.add_to_context(self, {'cw_quantity': -cw_quantity})
                    available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                              lot_id=ml.lot_id,
                                                                              package_id=ml.package_id,
                                                                              owner_id=ml.owner_id)
                    if available_qty < 0 and ml.lot_id:
                        untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                      package_id=ml.package_id, owner_id=ml.owner_id,
                                                                      strict=True)
                        cw_untracked_qty = Quant._get_available_cw_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                            package_id=ml.package_id,
                                                                            owner_id=ml.owner_id,
                                                                            strict=True)
                        if untracked_qty:
                            cw_taken_from_untracked_qty = min(cw_untracked_qty, abs(cw_quantity))
                            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                            catch_weight.add_to_context(self, {'cw_quantity': -cw_taken_from_untracked_qty})
                            Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                             lot_id=False, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                            catch_weight.add_to_context(self, {'cw_quantity': cw_taken_from_untracked_qty})
                            Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                             lot_id=ml.lot_id, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                    catch_weight.add_to_context(self, {'cw_quantity': cw_quantity})
                    Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                     package_id=ml.result_package_id, owner_id=ml.owner_id,
                                                     in_date=in_date)
                done_ml |= ml
            (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
                'product_uom_qty': 0.00,
                'product_cw_uom_qty': 0.00,
                'date': fields.Datetime.now(),
            })

