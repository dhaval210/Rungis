# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.addons.tis_catch_weight.models import catch_weight


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def write(self, vals):
        """ Through the interface, we allow users to change the charateristics of a move line. If a
        quantity has been reserved for this move line, we impact the reservation directly to free
        the old quants and allocate the new ones.
        """
        if (
            'dummy_id' in vals and
            'move_id' not in vals and
            'picking_id' in vals and
            'product_id' in vals
        ):
            move_ids = self.env['stock.move'].search(
                [
                    ('product_id', '=', vals['product_id']),
                    ('picking_id', '=', vals['picking_id'])
                ],
                limit=1
            )
            vals['move_id'] = move_ids[0].id
        if self.env.context.get('bypass_reservation_update'):
            return super(StockMoveLine, self).write(vals)

        Quant = self.env['stock.quant']
        precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
        # We forbid to change the reserved quantity in the interace, but it is needed in the
        # case of stock.move's split.
        # TODO Move me in the update        
        if 'product_cw_uom_qty' in vals:
            for ml in self.filtered(
                    lambda m: m.state in ('partially_available', 'assigned') and m.product_id.type == 'product' and m.product_id._is_cw_product()):
                if not ml.location_id.should_bypass_reservation():
                    # - vals['product_cw_uom_qty']
                    cw_qty_to_decrease = ml.cw_product_qty - ml.product_cw_uom._compute_quantity(vals['product_cw_uom_qty'], ml.product_id.cw_uom_id, rounding_method='HALF-UP')
                    qty_to_decrease = ml.product_qty - vals['product_uom_qty']
                    try:
                        Quant._update_reserved_cw_quantity(ml.product_id, ml.location_id, -cw_qty_to_decrease,
                                                           -qty_to_decrease, lot_id=ml.lot_id, package_id=ml.package_id,
                                                           owner_id=ml.owner_id, strict=True)
                    except UserError:
                        if ml.lot_id:
                            Quant._update_reserved_cw_quantity(ml.product_id, ml.location_id, -cw_qty_to_decrease,
                                                               -qty_to_decrease, lot_id=False, package_id=ml.package_id,
                                                               owner_id=ml.owner_id, strict=True)
                        else:
                            raise
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.production.lot'),
            ('package_id', 'stock.quant.package'),
            ('result_package_id', 'stock.quant.package'),
            ('owner_id', 'res.partner')
        ]
        updates = {}
        for key, model in triggers:
            if key in vals:
                updates[key] = self.env[model].browse(vals[key])
        if updates:
            for ml in self.filtered(
                    lambda ml: ml.state in ['partially_available', 'assigned'] and ml.product_id.type == 'product' and ml.product_id._is_cw_product()):
                if not ml.location_id.should_bypass_reservation():
                    try:
                        Quant._update_reserved_cw_quantity(ml.product_id, ml.location_id, -ml.cw_product_qty,
                                                           -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id,
                                                           owner_id=ml.owner_id, strict=True)
                    except UserError:
                        if ml.lot_id:
                            Quant._update_reserved_cw_quantity(ml.product_id, ml.location_id, -ml.cw_product_qty,
                                                               -ml.product_qty, lot_id=False, package_id=ml.package_id,
                                                               owner_id=ml.owner_id, strict=True)
                        else:
                            raise
                if not updates.get('location_id', ml.location_id).should_bypass_reservation():
                    new_product_cw_qty = 0
                    try:
                        q = Quant._update_reserved_cw_quantity(ml.product_id,
                                                               updates.get('location_id', ml.location_id),
                                                               ml.cw_product_qty,
                                                               ml.product_qty,
                                                               lot_id=updates.get('lot_id', ml.lot_id),
                                                               package_id=updates.get('package_id', ml.package_id),
                                                               owner_id=updates.get('owner_id', ml.owner_id),
                                                               strict=True)
                        new_product_cw_qty = sum([x[1] for x in q])
                    except UserError:
                        if updates.get('lot_id'):
                            try:
                                q = Quant._update_reserved_cw_quantity(ml.product_id,
                                                                       updates.get('location_id', ml.location_id),
                                                                       ml.cw_product_qty,
                                                                       ml.product_qty,
                                                                       lot_id=False,
                                                                       package_id=updates.get('package_id',
                                                                                              ml.package_id),
                                                                       owner_id=updates.get('owner_id', ml.owner_id),
                                                                       strict=True)
                                new_product_cw_qty = sum([x[1] for x in q])
                            except UserError:
                                pass
                    if new_product_cw_qty != ml.cw_product_qty:
                        # new_product_cw_qty
                        new_product_uom_qty = ml.product_id.cw_uom_id._compute_quantity(new_product_cw_qty, ml.product_cw_uom, rounding_method='HALF-UP')
                        ml.with_context(bypass_reservation_update=True).product_cw_uom_qty = new_product_uom_qty

        # When editing a done move line, the reserved availability of a potential chained move is impacted. Take care of running again `_action_assign` on the concerned moves.
        next_moves = self.env['stock.move']                        
        if updates or 'cw_qty_done' in vals:
            # for ml in self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.type == 'product' and ml.product_id._is_cw_product()):
            mls = self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.type == 'product' and ml.product_id._is_cw_product())
            if not updates:  # we can skip those where qty_done is already good up to UoM rounding
                mls = mls.filtered(lambda ml: not float_is_zero(ml.cw_qty_done - vals['cw_qty_done'], precision_rounding=ml.product_cw_uom.rounding))
            for ml in mls:
                cw_qty_done_orig = ml.cw_qty_done
                in_date = Quant._update_available_cw_quantity(ml.product_id, ml.location_dest_id, -cw_qty_done_orig,
                                                              lot_id=ml.lot_id,
                                                              package_id=ml.result_package_id, owner_id=ml.owner_id)[1]
                Quant._update_available_cw_quantity(ml.product_id, ml.location_id, cw_qty_done_orig, lot_id=ml.lot_id,
                                                    package_id=ml.package_id, owner_id=ml.owner_id, in_date=in_date)
                # move what's been actually done                                                    
                product_id = ml.product_id
                location_id = updates.get('location_id', ml.location_id)
                location_dest_id = updates.get('location_dest_id', ml.location_dest_id)
                cw_qty_done = vals.get('cw_qty_done', ml.cw_qty_done)
                lot_id = updates.get('lot_id', ml.lot_id)
                package_id = updates.get('package_id', ml.package_id)
                result_package_id = updates.get('result_package_id', ml.result_package_id)
                owner_id = updates.get('owner_id', ml.owner_id)
                cw_quantity = cw_qty_done
                if not float_is_zero(cw_quantity, precision_digits=precision):
                    available_cw_qty, in_date = Quant._update_available_cw_quantity(product_id, location_id,
                                                                                    -cw_quantity, lot_id=lot_id,
                                                                                    package_id=package_id,
                                                                                    owner_id=owner_id)
                    if available_cw_qty < 0 and lot_id:
                        untracked_cw_qty = Quant._get_available_cw_quantity(product_id, location_id, lot_id=False,
                                                                            package_id=package_id, owner_id=owner_id,
                                                                            strict=True)
                        if untracked_cw_qty:
                            taken_from_untracked_cw_qty = min(untracked_cw_qty, abs(available_cw_qty))
                            Quant._update_available_cw_quantity(product_id, location_id, -taken_from_untracked_cw_qty,
                                                                lot_id=False, package_id=package_id, owner_id=owner_id)
                            Quant._update_available_cw_quantity(product_id, location_id, taken_from_untracked_cw_qty,
                                                                lot_id=lot_id, package_id=package_id, owner_id=owner_id)
                    Quant._update_available_cw_quantity(product_id, location_dest_id, cw_quantity, lot_id=lot_id,
                                                        package_id=result_package_id, owner_id=owner_id,
                                                        in_date=in_date)

        moves_to_update = {}
        candidates_dict = {}
        move_valss = {}
        ifcandidates = {'candidates': 1}
        if 'cw_qty_done' in vals:
            for move_line in self.filtered(
                    lambda ml: ml.state == 'done' and (ml.move_id._is_in() or ml.move_id._is_out())):
                moves_to_update[move_line.move_id] = vals['cw_qty_done'] - move_line.cw_qty_done

            for move_id, qty_difference in moves_to_update.items():
                if move_id.product_id.cost_method in ['standard', 'average']:
                    correction_value = qty_difference * move_id.product_id.standard_price
                    if move_id._is_in():
                        move_valss['value'] = move_id.value + correction_value
                    elif move_id._is_out():
                        move_valss['value'] = move_id.value - correction_value
                else:
                    if move_id._is_in():
                        correction_value = qty_difference * move_id.price_unit
                        new_remaining_value = move_id.remaining_value + correction_value
                        move_valss['value'] = move_id.value + correction_value
                        move_valss['remaining_qty'] = move_id.remaining_qty + qty_difference
                        move_valss['remaining_value'] = move_id.remaining_value + correction_value
                    elif move_id._is_out() and qty_difference > 0:
                        correction_value = self.env['stock.move']._run_fifo(move_id, quantity=qty_difference)
                        move_valss['value'] = move_id.value - correction_value
                    elif move_id._is_out() and qty_difference < 0:
                        candidates_receipt = self.env['stock.move'].search(move_id._get_in_domain(),
                                                                           order='date, id desc', limit=1)
                        ifcandidates['candidates'] = candidates_receipt
                        if candidates_receipt:
                            candidates_dict['remaining_qty'] = candidates_receipt.remaining_qty + -qty_difference,
                            candidates_dict['remaining_value'] = candidates_receipt.remaining_value + (
                                    -qty_difference * candidates_receipt.price_unit),
                            correction_value = qty_difference * candidates_receipt.price_unit
                        else:
                            correction_value = qty_difference * move_id.product_id.standard_price
                        move_valss['value'] = move_id.value - correction_value
        res = super(StockMoveLine, self).write(vals)
        cw_context = self._context.get('cw_params')
        if 'cw_qty_done' in vals:
            for move_id, qty_difference in moves_to_update.items():
                if move_id.product_id.valuation == 'real_time':
                    cw_context.update({
                        'cw_qty_done_account_move_write': vals['cw_qty_done'] or 0})
                else:
                    if ifcandidates.get('candidates') != 0:
                        candidates = ifcandidates.get('candidates')
                        candidates.write(candidates_dict)
                move_id.write(move_valss)
        if 'cw_qty_done' in vals:
            for move in self.mapped('move_id'):
                if move.scrapped:
                    move.scrap_ids.write({'scrap_cw_qty': move.cw_qty_done})

        if updates or 'cw_qty_done' in vals:
            moves = self.filtered(lambda ml: ml.move_id.state == 'done').mapped('move_id')
            for move in moves:
                move.product_cw_uom_qty = move.cw_qty_done
        return res

    @api.model
    def create(self, vals):
        if (
            'dummy_id' in vals and
            'move_id' not in vals and
            'picking_id' in vals and
            'product_id' in vals
        ):
            move_ids = self.env['stock.move'].search(
                [
                    ('product_id', '=', vals['product_id']),
                    ('picking_id', '=', vals['picking_id'])
                ],
                limit=1
            )
            vals['move_id'] = move_ids[0].id

        if 'product_id' in vals:
            product_data = self.env['product.product'].browse(vals['product_id'])
        if (
            not self.env.user.has_group('tis_catch_weight.group_catch_weight') or
            (
                product_data.id is not False and
                not product_data._is_cw_product()
            )
        ):
            return super(StockMoveLine, self).create(vals)
        else:
            if 'cw_qty_done' in vals:
                catch_weight.add_to_context(self, {'account_quantity_done': vals['cw_qty_done'] or 0})
            vals['ordered_cw_qty'] = vals.get('product_cw_uom_qty')
            create_flag = 0
            if 'picking_id' in vals and not vals.get('move_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.state == 'done':
                    create_flag = 1
            mls = super(StockMoveLine, self).create(vals)
            for ml in mls:            
                if create_flag == 1:
                    ml.move_id.move_line_ids.write({
                        'product_cw_uom_qty': 'cw_qty_done' in vals and vals['cw_qty_done'] or 0, # custom hucke set this!
                        'product_cw_uom': vals['product_cw_uom'],
                    })
                if ml.state == 'done':
                    if ml.product_id.type == 'product':
                        Quant = self.env['stock.quant']
                        cw_quantity = ml.cw_qty_done
                        in_date = None
                        cw_available_qty, in_date = Quant._update_available_cw_quantity(ml.product_id, ml.location_id,
                                                                                        -cw_quantity,
                                                                                        lot_id=ml.lot_id,
                                                                                        package_id=ml.package_id,
                                                                                        owner_id=ml.owner_id)
                        if cw_available_qty < 0 and ml.lot_id:
                            untracked_cw_qty = Quant._get_available_cw_quantity(ml.product_id, ml.location_id,
                                                                                lot_id=False, package_id=ml.package_id,
                                                                                owner_id=ml.owner_id, strict=True)
                            if untracked_cw_qty:
                                taken_from_untracked_cw_qty = min(untracked_cw_qty, abs(cw_quantity))
                                Quant._update_available_cw_quantity(ml.product_id, ml.location_id,
                                                                    -taken_from_untracked_cw_qty, lot_id=False,
                                                                    package_id=ml.package_id, owner_id=ml.owner_id)
                                Quant._update_available_cw_quantity(ml.product_id, ml.location_id,
                                                                    taken_from_untracked_cw_qty, lot_id=ml.lot_id,
                                                                    package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_cw_quantity(ml.product_id, ml.location_dest_id, cw_quantity,
                                                            lot_id=ml.lot_id, package_id=ml.result_package_id,
                                                            owner_id=ml.owner_id, in_date=in_date)
            return mls

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
                                    lot = self.env['stock.production.lot'].create(
                                        {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                    )
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
