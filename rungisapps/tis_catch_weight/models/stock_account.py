# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt. Ltd.(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _run_fifo(self, move, quantity=None):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(StockMove, self)._run_fifo(move, quantity=None)
        move.ensure_one()
        if not move.product_id._is_price_based_on_cw('purchase'):
            return super(StockMove, self)._run_fifo(move, quantity=None)
        valued_move_lines = move.move_line_ids.filtered(
            lambda
                ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_cw_uom._compute_quantity(valued_move_line.cw_qty_done,
                                                                                 move.product_id.cw_uom_id)
        qty_to_take_on_candidates = quantity or valued_quantity
        candidates = move.product_id._get_fifo_candidates_in_move_with_company(move.company_id.id)
        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        for candidate in candidates:
            new_standard_price = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates

            candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
            value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
            candidate_vals = {
                'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                'remaining_value': candidate.remaining_value - value_taken_on_candidate,
            }
            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            if qty_to_take_on_candidates == 0:
                break

        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.sudo().with_context(force_company=move.company_id.id) \
                .standard_price = new_standard_price

        if qty_to_take_on_candidates == 0:
            move.write({
                'value': -tmp_value if not quantity else move.value or -tmp_value,
                'price_unit': -tmp_value / move.product_qty,
            })
        elif qty_to_take_on_candidates > 0:
            last_fifo_price = new_standard_price or move.product_id.standard_price
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            vals = {
                'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
                'remaining_value': move.remaining_value + negative_stock_value,
                'value': -tmp_value,
                'price_unit': -1 * last_fifo_price,
            }
            move.write(vals)
        return tmp_value

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        cw_quantity = self.env.context.get('forced_quantity', self.cw_product_qty)
        cw_quantity = cw_quantity if self._is_in() else -1 * cw_quantity
        x = res[0][2]
        x.update({
            'cw_quantity': cw_quantity,
        })
        y = res[1][2]
        y.update({
            'cw_quantity': cw_quantity,
        })
        if len(res) > 2:
            z = res[2][2]
            z.update({
                'cw_quantity': cw_quantity,
            })
        return res


    def _run_valuation(self, quantity=None):
        if self.product_id._is_price_based_on_cw('purchase'):
            if quantity != None:
                params = self._context.get('cw_params')
                if 'account_quantity_done' in params:
                    quantity = params.get('account_quantity_done')
            self.ensure_one()
            if self._is_in():
                valued_move_lines = self.move_line_ids.filtered(
                    lambda
                        ml: not ml.location_id._should_be_valued() and ml.location_dest_id._should_be_valued() and not ml.owner_id)
                valued_quantity = 0
                for valued_move_line in valued_move_lines:
                    valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.cw_qty_done,
                                                                                         self.product_id.uom_id)
                vals = {}
                price_unit = self._get_price_unit()
                value = price_unit * (quantity or valued_quantity)
                vals = {'price_unit': price_unit,
                        'value': value if quantity is None or not self.value else self.value,
                        'remaining_value': value if quantity is None else self.remaining_value + value,
                        'remaining_qty': valued_quantity if quantity is None else self.remaining_qty + quantity
                        }
                if self.product_id.cost_method == 'standard':
                    value = self.product_id.standard_price * (quantity or valued_quantity)
                    vals.update({
                        'price_unit': self.product_id.standard_price,
                        'value': value if quantity is None or not self.value else self.value,
                    })
                self.write(vals)
            elif self._is_out():
                valued_move_lines = self.move_line_ids.filtered(
                    lambda
                        ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
                valued_quantity = 0
                for valued_move_line in valued_move_lines:
                    valued_quantity += valued_move_line.product_cw_uom._compute_quantity(valued_move_line.cw_qty_done,
                                                                                         self.product_id.cw_uom_id)
                self.env['stock.move']._run_fifo(self, quantity=quantity)
                if self.product_id.cost_method in ['standard', 'average']:
                    curr_rounding = self.company_id.currency_id.rounding
                    value = -float_round(
                        self.product_id.standard_price * (valued_quantity if quantity is None else quantity),
                        precision_rounding=curr_rounding)
                    self.write({
                        'value': value if quantity is None else self.value + value,
                    })
                    if valued_quantity > 0:
                        self.write({
                            'price_unit': value / valued_quantity,
                        })
            elif self._is_dropshipped() or self._is_dropshipped_returned():
                curr_rounding = self.company_id.currency_id.rounding
                if self.product_id.cost_method in ['fifo']:
                    price_unit = self._get_price_unit()
                    self.product_id.standard_price = price_unit
                else:
                    price_unit = self.product_id.standard_price
                value = float_round(self.cw_product_qty * price_unit, precision_rounding=curr_rounding)
                self.write({
                    'value': value if self._is_dropshipped() else -value,
                    'price_unit': price_unit if self._is_dropshipped() else -price_unit,
                })
        else:
            return super(StockMove, self)._run_valuation(quantity=None)

    def _account_entry_move(self):
        if self.product_id._is_price_based_on_cw('purchase'):
            cw_context = self._context.get('cw_params')
            if cw_context and 'cw_qty_done_account_move_write' in cw_context:
                cw_qty_done = cw_context.get('cw_qty_done_account_move_write')
                moves_to_update = {}
                for move_line in self.move_line_ids.filtered(
                        lambda ml: ml.state == 'done' and (ml.move_id._is_in() or ml.move_id._is_out())):
                    moves_to_update[move_line.move_id] = cw_qty_done - move_line.cw_qty_done
                for move_id, qty_difference in moves_to_update.items():
                    move_vals = {}
                    if move_id.product_id.cost_method in ['standard', 'average']:
                        correction_value = qty_difference * move_id.product_id.standard_price
                        if move_id._is_in():
                            move_vals['value'] = move_id.value + correction_value
                        elif move_id._is_out():
                            move_vals['value'] = move_id.value - correction_value
                    else:
                        if move_id._is_in():
                            correction_value = qty_difference * move_id.price_unit
                            new_remaining_value = move_id.remaining_value + correction_value
                            move_vals['value'] = move_id.value + correction_value
                            move_vals['remaining_qty'] = move_id.remaining_qty + qty_difference
                            move_vals['remaining_value'] = move_id.remaining_value + correction_value
                        elif move_id._is_out() and qty_difference > 0:
                            correction_value = self.env['stock.move']._run_fifo(move_id, quantity=qty_difference)
                            move_vals['value'] = move_id.value - correction_value
                        elif move_id._is_out() and qty_difference < 0:
                            candidates_receipt = self.env['stock.move'].search(move_id._get_in_domain(),
                                                                               order='date, id desc', limit=1)
                            if candidates_receipt:
                                candidates_receipt.write({
                                    'remaining_qty': candidates_receipt.remaining_qty + -qty_difference,
                                    'remaining_value': candidates_receipt.remaining_value + (
                                            -qty_difference * candidates_receipt.price_unit),
                                })
                                correction_value = qty_difference * candidates_receipt.price_unit
                            else:
                                correction_value = qty_difference * move_id.product_id.standard_price
                            move_vals['value'] = move_id.value - correction_value
                    move_id.write(move_vals)

                    if move_id.product_id.valuation == 'real_time':
                        move_id.with_context(force_valuation_amount=correction_value, forced_quantity=qty_difference)
                    if qty_difference > 0:
                        move_id.product_price_update_before_done(forced_qty=qty_difference)
        return super(StockMove, self)._account_entry_move()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cw_qty_at_date = fields.Float('CW Quantity', compute='_compute_cw_stock_qty')

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.cw_product_qty', 'stock_move_ids.state',
                 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method',
                 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        super(ProductProduct, self)._compute_stock_value()
        to_date = self.env.context.get('to_date')
        for product in self:
            if product._is_price_based_on_cw('purchase'):
                if product.cost_method in ['standard', 'average']:
                    cw_qty_available = product.with_context(company_owned=True, owner_id=False).cw_qty_available
                    price_used = product.standard_price
                    if to_date:
                        price_used = product.get_history_price(
                            self.env.user.company_id.id,
                            date=to_date,
                        )
                    product.stock_value = price_used * cw_qty_available

    @api.multi
    @api.depends('stock_move_ids.cw_product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method',
                 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_cw_stock_qty(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT
                        aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit),
                        sum(cw_quantity), array_agg(aml.id)
                    FROM account_move_line AS aml
                    WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                    GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        for product in self:
            if product._is_cw_product():
                if product.cost_method in ['standard', 'average']:
                    qty_available = product.with_context(company_owned=True, owner_id=False).cw_qty_available
                    product.cw_qty_at_date = qty_available
                elif product.cost_method == 'fifo':
                    if to_date:
                        if product.product_tmpl_id.valuation == 'manual_periodic':
                            product.cw_qty_at_date = product.with_context(company_owned=True,
                                                                          owner_id=False).cw_qty_available
                        elif product.product_tmpl_id.valuation == 'real_time':
                            valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                            value, quantity, aml_ids = fifo_automated_values.get(
                                (product.id, valuation_account_id)) or (0, 0, [])
                            product.cw_qty_at_date = quantity
                    else:
                        product.cw_qty_at_date = product.with_context(company_owned=True,
                                                                      owner_id=False).cw_qty_available
            else:
                product.cw_qty_at_date = False

    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        res = super(ProductProduct, self)._convert_prepared_anglosaxon_line(line, partner)
        res.update({
            'cw_quantity': line.get('cw_quantity', 1.00),
        })
        return res
