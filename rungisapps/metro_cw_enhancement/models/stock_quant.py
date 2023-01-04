# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from psycopg2 import OperationalError
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None):
        if (
            not self.env.user.has_group('tis_catch_weight.group_catch_weight') or
            not product_id._is_cw_product()
        ):
            return super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id,
                                                                      package_id=package_id, owner_id=owner_id,
                                                                      in_date=in_date)
        else:
            cw_params = self._context.get('cw_params')
            if 'cw_quantity' in cw_params.keys():
                cw_quantity = cw_params['cw_quantity']
                del cw_params['cw_quantity']

                self = self.sudo()
                quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                      strict=True)
                rounding = product_id.uom_id.rounding

                incoming_dates = [d for d in quants.mapped('in_date') if d]
                incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
                if in_date:
                    incoming_dates += [in_date]
                if incoming_dates:
                    in_date = fields.Datetime.to_string(min(incoming_dates))
                else:
                    in_date = fields.Datetime.now()
                for quant in quants:
                    try:
                        with self._cr.savepoint():
                            self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                             log_exceptions=False)
                            quant.write({
                                'quantity': quant.quantity + quantity,
                                'in_date': in_date,
                                'cw_stock_quantity': quant.cw_stock_quantity + cw_quantity,
                            })
                            if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(
                                    quant.reserved_quantity, precision_rounding=rounding):
                                quant.unlink()
                            break
                    except OperationalError as e:
                        if e.pgcode == '55P03':  # could not obtain the lock
                            continue
                        else:
                            raise
                else:
                    self.create({
                        'product_id': product_id.id,
                        'location_id': location_id.id,
                        'quantity': quantity,
                        'cw_stock_quantity': cw_quantity,
                        'lot_id': lot_id and lot_id.id,
                        'package_id': package_id and package_id.id,
                        'owner_id': owner_id and owner_id.id,
                        'in_date': in_date,
                    })
                return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                                    owner_id=owner_id, strict=False,
                                                    allow_negative=True), fields.Datetime.from_string(in_date)
            else:
                return super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity,
                                                                          lot_id=lot_id, package_id=package_id,
                                                                          owner_id=owner_id, in_date=in_date)

    @api.model
    def _update_available_cw_quantity(self, product_id, location_id, cw_quantity, lot_id=None, package_id=None,
                                      owner_id=None,
                                      in_date=None):
        if (
            not self.env.user.has_group('tis_catch_weight.group_catch_weight') or
            not product_id._is_cw_product()
        ):
            return
        else:

            self = self.sudo()
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                  strict=True)
            rounding = product_id.uom_id.rounding
            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'cw_stock_quantity': quant.cw_stock_quantity + cw_quantity,
                        })
                        if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(
                                quant.reserved_quantity, precision_rounding=rounding):
                            quant.unlink()
                        break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise
            else:
                self.create({
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'quantity': 0.0,
                    'cw_stock_quantity': cw_quantity,
                    'lot_id': lot_id and lot_id.id,
                    'package_id': package_id and package_id.id,
                    'owner_id': owner_id and owner_id.id,
                    'in_date': in_date,
                })
            return self._get_available_cw_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                                   owner_id=owner_id, strict=False,
                                                   allow_negative=True), fields.Datetime.from_string(in_date)

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                  strict=False):
        if (
            not self.env.user.has_group('tis_catch_weight.group_catch_weight') or
            not product_id._is_cw_product()
        ):
            # if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id=lot_id,
                                                                     package_id=package_id, owner_id=owner_id,
                                                                     strict=strict)
        else:
            cw_params = self._context.get('cw_params')
            if cw_params and 'cw_reserved_quantity' in cw_params.keys():
                cw_quantity = cw_params['cw_reserved_quantity']
                cw_params.pop('cw_reserved_quantity', None)

                self = self.sudo()
                rounding = product_id.uom_id.rounding
                quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                      strict=strict)
                reserved_quants = []
                if float_compare(quantity, 0, precision_rounding=rounding) or (cw_quantity - 0) > 0:
                    available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id,
                                                                      package_id=package_id, owner_id=owner_id,
                                                                      strict=strict)
                    available_cw_quantity = self._get_available_cw_quantity(product_id, location_id, lot_id=lot_id,
                                                                            package_id=package_id, owner_id=owner_id,
                                                                            strict=strict)

                    if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                        raise UserError(_(
                            'It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
                    if float_compare(cw_quantity, available_cw_quantity, precision_rounding=rounding) > 0:
                        raise UserError(_(
                            'It is not possible to reserve more products of %s than CW quantity you have in stock.') % product_id.display_name)
                elif float_compare(quantity, 0, precision_rounding=rounding) and (cw_quantity - 0) < 0:
                    available_quantity = sum(quants.mapped('reserved_quantity'))
                    if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                        raise UserError(_(
                            'It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
                    available_cw_quantity = sum(quants.mapped('cw_stock_reserved_quantity'))
                    if (abs(cw_quantity) - available_cw_quantity) > 0:
                        raise UserError(_(
                            'It is not possible to unreserve more products of %s than CW Quantity you have  in stock.') % product_id.display_name)
                else:
                    return reserved_quants
                for quant in quants:
                    if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                        max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                        if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                            continue
                        max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                        quant.reserved_quantity += max_quantity_on_quant
                        reserved_quants.append((quant, max_quantity_on_quant))
                        quantity -= max_quantity_on_quant
                        available_quantity -= max_quantity_on_quant
                        max_cw_quantity_on_quant = quant.cw_stock_quantity - quant.cw_stock_reserved_quantity
                        if float_compare(max_cw_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                            continue
                        max_cw_quantity_on_quant = min(max_cw_quantity_on_quant, cw_quantity)
                        quant.cw_stock_reserved_quantity += max_cw_quantity_on_quant
                        reserved_quants.append((quant, max_cw_quantity_on_quant))
                        cw_quantity -= max_cw_quantity_on_quant
                        available_cw_quantity -= max_cw_quantity_on_quant
                    else:
                        max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                        quant.reserved_quantity -= max_quantity_on_quant
                        reserved_quants.append((quant, -max_quantity_on_quant))
                        quantity += max_quantity_on_quant
                        available_quantity += max_quantity_on_quant
                        max_cw_quantity_on_quant = min(quant.cw_stock_reserved_quantity, abs(cw_quantity))
                        quant.cw_stock_reserved_quantity -= max_cw_quantity_on_quant
                        reserved_quants.append((quant, -max_cw_quantity_on_quant))
                        cw_quantity += max_cw_quantity_on_quant
                        available_cw_quantity += max_cw_quantity_on_quant

                    if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity,
                                                                                             precision_rounding=rounding):
                        break
                    if float_is_zero(cw_quantity, precision_rounding=rounding) or float_is_zero(available_cw_quantity,
                                                                                                precision_rounding=rounding):
                        break
                return reserved_quants
            else:
                res = super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity,
                                                                        lot_id=lot_id, package_id=package_id,
                                                                        owner_id=owner_id,
                                                                        strict=strict)
                return res

    @api.model
    def _update_reserved_cw_quantity(self, product_id, location_id, cw_quantity, quantity, lot_id=None, package_id=None,
                                     owner_id=None,
                                     strict=False):
        cw_params = self._context.get('cw_params')
        if (
            not self.env.user.has_group('tis_catch_weight.group_catch_weight') or
            not product_id._is_cw_product()
        ):
            return []
        else:

            self = self.sudo()
            rounding = product_id.cw_uom_id.rounding
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                  strict=strict)
            cw_reserved_quants = []

            if float_compare(cw_quantity, 0, precision_rounding=rounding) > 0:
                available_cw_quantity = self._get_available_cw_quantity(product_id, location_id, lot_id=lot_id,
                                                                        package_id=package_id, owner_id=owner_id,
                                                                        strict=strict)
                # available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id,
                #                                                   package_id=package_id, owner_id=owner_id,
                #                                                   strict=strict)
                if float_compare(cw_quantity, available_cw_quantity, precision_rounding=rounding) > 0:
                    raise UserError(_(
                        'It is not possible to reserve more products of %s than CW Quantity you have in stock.') % product_id.display_name)
            elif float_compare(cw_quantity, 0, precision_rounding=rounding) < 0:
                available_cw_quantity = sum(quants.mapped('cw_stock_reserved_quantity'))
                # available_quantity = sum(quants.mapped('reserved_quantity'))
                if float_compare(abs(cw_quantity), available_cw_quantity, precision_rounding=rounding) > 0:
                    raise UserError(_(
                        'It is not possible to unreserve more products of %s than CW Quantity you have in stock.') % product_id.display_name)
            else:
                return cw_reserved_quants
            for quant in quants:
                if float_compare(cw_quantity, 0, precision_rounding=rounding) > 0:
                    max_cw_quantity_on_quant = quant.cw_stock_quantity - quant.cw_stock_reserved_quantity
                    if product_id.tracking == 'serial':
                        if quant.lot_id:
                            max_cw_quantity_on_quant = quant.cw_stock_quantity
                        else:
                            continue

                    if (
                        quantity > 0 and
                        quant.quantity == quant.reserved_quantity and
                        quant.quantity == quantity and
                        quant.cw_stock_reserved_quantity == 0 and
                        quant.cw_stock_quantity == cw_quantity
                    ):
                        max_qty = quantity
                    else:
                        max_qty = quant.quantity - quant.reserved_quantity

                    if max_qty < quantity and max_qty != 0:                        
                        max_cw_theoretical = round(max_qty * product_id.average_cw_quantity, 3)
                        max_cw_quantity_on_quant = min(max_cw_quantity_on_quant, max_cw_theoretical)
                    elif max_qty == 0 and cw_params is not None and quant.id in cw_params and cw_params[quant.id] == cw_quantity:
                        max_cw_quantity_on_quant = min(max_cw_quantity_on_quant, cw_quantity)
                    elif max_qty == 0:
                        continue
                    # max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                    if float_compare(max_cw_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                        continue
                    # if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    #     continue
                    max_cw_quantity_on_quant = min(max_cw_quantity_on_quant, cw_quantity)
                    # max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                    quant.cw_stock_reserved_quantity = round(quant.cw_stock_reserved_quantity + max_cw_quantity_on_quant, 3)
                    cw_reserved_quants.append((quant, max_cw_quantity_on_quant))
                    cw_quantity = round(cw_quantity - max_cw_quantity_on_quant, 3)
                    quantity -= max_qty
                    # available_quantity -= max_quantity_on_quant
                else:
                    max_cw_quantity_on_quant = min(quant.cw_stock_reserved_quantity, abs(cw_quantity))
                    if product_id.tracking == 'serial':
                        max_cw_quantity_on_quant = quant.cw_stock_reserved_quantity
                    # max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                    quant.cw_stock_reserved_quantity = round(quant.cw_stock_reserved_quantity - max_cw_quantity_on_quant, 3)

                    cw_reserved_quants.append((quant, -max_cw_quantity_on_quant))
                    cw_quantity = round(cw_quantity + max_cw_quantity_on_quant, 3)
                    # quantity += max_quantity_on_quant
                    available_cw_quantity = round(available_cw_quantity + max_cw_quantity_on_quant, 3)
                    # available_quantity += max_quantity_on_quant

                if float_is_zero(cw_quantity, precision_rounding=rounding) or float_is_zero(available_cw_quantity,
                                                                                            precision_rounding=rounding):
                    break
                # if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity,
                #                                                                          precision_rounding=rounding):
                #     break
            return cw_reserved_quants

    @api.model
    def _get_available_cw_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None,
                                   strict=False, allow_negative=False):

        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        quants = quants.filtered(lambda x: (x.quantity - x.reserved_quantity) >= 0)
        rounding = product_id.cw_uom_id.rounding
        if product_id.tracking == 'none':
            available_cw_quantity = sum(quants.mapped('cw_stock_quantity')) - sum(
                quants.mapped('cw_stock_reserved_quantity'))
            if allow_negative:
                return available_cw_quantity
            else:
                return available_cw_quantity if float_compare(available_cw_quantity, 0.0,
                                                              precision_rounding=rounding) >= 0.0 else 0.0
        else:
            availaible_cw_quantities = {lot_id: 0.0 for lot_id in list(set(quants.mapped('lot_id'))) + ['untracked']}
            for quant in quants:
                if not quant.lot_id:
                    availaible_cw_quantities['untracked'] += quant.cw_stock_quantity - quant.cw_stock_reserved_quantity
                else:
                    availaible_cw_quantities[quant.lot_id] += quant.cw_stock_quantity - quant.cw_stock_reserved_quantity
            if allow_negative:
                return sum(availaible_cw_quantities.values())
            else:
                return sum([available_cw_quantity for available_cw_quantity in availaible_cw_quantities.values() if
                            float_compare(available_cw_quantity, 0, precision_rounding=rounding) > 0])
