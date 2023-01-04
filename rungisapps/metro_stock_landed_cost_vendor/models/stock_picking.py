# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        if self.partner_id.landed_cost_line_ids or self.partner_id.later_income_line_ids:
            self._create_landed_cost()
        return res

    def _create_landed_cost(self):
        for pick in self:
            # Only applicable for Receipts
            if pick.picking_type_code == 'incoming':
                total_amount = sum(
                    [x.qty_done * x.move_id.purchase_line_id.price_unit for
                     x in pick.move_line_ids])
                # Create landed cost & validate it
                if self.partner_id.landed_cost_line_ids:
                    landed_cost = self.env['stock.landed.cost'].create(
                        pick._prepare_landed_cost(total_amount))
                    landed_cost.compute_landed_cost()
                    landed_cost.button_validate()
                if self.partner_id.later_income_line_ids:
                    later_income = self.env['stock.landed.cost'].create(
                        pick._prepare_later_income(total_amount))
                    later_income.compute_landed_cost()
                    later_income.button_validate()
        return True

    def _prepare_landed_cost_lines(self, vendor, amount):
        cost_lines = []
        for line in vendor.landed_cost_line_ids:
            product = line.product_id
            account = (
                product.property_account_expense_id.id or
                product.categ_id.property_account_expense_categ_id.id
            )
            values = {
                'product_id': product.id,
                'split_method': product.split_method,
                'account_id': account,
                'price_unit': float((amount or 0.0) * line.percentage) / 100.0,
                'name': product.name,
            }
            cost_lines.append((0, 0, values))
        return cost_lines

    def _prepare_later_income_lines(self, vendor, amount):
        cost_lines = []
        for line in vendor.later_income_line_ids:
            product = line.product_id
            account = (
                product.property_account_expense_id.id or
                product.categ_id.property_account_expense_categ_id.id
            )
            values = {
                'product_id': product.id,
                'split_method': product.split_method,
                'account_id': account,
                'price_unit': float((amount or 0.0) * line.percentage) / 100.0,
                'name': product.name,
            }
            cost_lines.append((0, 0, values))
        return cost_lines

    def _prepare_landed_cost(self, amount):
        if self.partner_id.landed_cost_line_ids:
            if not self.company_id.landed_cost_journal_id:
                raise UserError(_("Missing Landed Cost Journal for company %s")
                                % self.company_id.name)
        return {
            'picking_ids': [(6, 0, [self.id])],
            'account_journal_id': self.company_id.landed_cost_journal_id.id,
            'cost_lines': self._prepare_landed_cost_lines(
                self.partner_id, amount)
        }

    def _prepare_later_income(self, amount):
        if self.partner_id.later_income_line_ids:
            if not self.company_id.later_income_journal_id:
                raise UserError(_("Missing Later Income Journal for company %s")
                                % self.company_id.name)
        return {
            'picking_ids': [(6, 0, [self.id])],
            'account_journal_id': self.company_id.later_income_journal_id.id,
            'cost_lines': self._prepare_later_income_lines(
                self.partner_id, amount)
        }
