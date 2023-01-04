# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open' and inv.type in ['in_invoice', 'in_refund'])
        if to_open_invoices.filtered(lambda inv: not all([il.account_analytic_id for il in inv.invoice_line_ids])):
            raise UserError(_("Please fill out the Analytic Account on all Vendor Bill lines."))
        return super(AccountInvoice, self).action_invoice_open()
