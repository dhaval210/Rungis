# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    disable_currency_onchange = fields.Boolean(string='Disable automatic currency calculation', default=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('debit', 'credit', 'currency_id', 'amount_currency')
    def _onchange_amount_currency(self):
        if not self.move_id.disable_currency_onchange:
            journal_currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id
            user_company = self.env.user.company_id
            if journal_currency_id and self.currency_id:
                rate = self.env['res.currency']._get_conversion_rate(journal_currency_id, self.currency_id, user_company, self.move_id.date)
                if self.debit:
                    self.amount_currency = self.debit * rate
                elif self.credit:
                    self.amount_currency = -self.credit * rate
                elif self.amount_currency and self.currency_id:
                    if self.amount_currency > 0 and not self.debit:
                        self.debit = self.amount_currency / rate
                        self.credit = 0
                    elif self.amount_currency < 0 and not self.credit:
                        self.debit = 0
                        self.credit = -self.amount_currency / rate
