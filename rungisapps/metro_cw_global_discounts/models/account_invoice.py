from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _prepare_refund_partial(self, invoice, date_invoice=None,
                                date=None, description=None, journal_id=None,
                                lines_id=None):
        res = super()._prepare_refund_partial(invoice, date_invoice, date, description, journal_id,lines_id)
        res['payment_term_id'] = invoice.payment_term_id and invoice.payment_term_id.id or False
        res['global_discount_ids'] = [(6, 0, invoice.global_discount_ids.ids)]
        return res

    @api.multi
    @api.returns('self')
    def refund_partial(self, date_invoice=None, date=None, description=None,
                       journal_id=None, lines_id=None):
        res = super().refund_partial(date_invoice, date, description, journal_id, lines_id)
        res._set_global_discounts_by_tax()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for r in self:
            # Compute correct taxes
            correct = r.get_taxes_values()
            # Get list of ids for correct taxes
            tax_ids = []
            old_tax_ids = []
            for correct_tax in correct.values():
                tax_ids.append(correct_tax["tax_id"])
            # unlink old taxes if they are not correct
            for t in r.tax_line_ids:
                old_tax_ids.append(t.tax_id.id)
                if not t.tax_id.id in tax_ids:
                    t.unlink()
            # Create new taxes if they were not existing before
            for c in correct.values():
                if not c["tax_id"] in old_tax_ids:
                    t = self.env["account.tax"].browse([c["tax_id"]])
                    self.env["account.invoice.tax"].create(c)
                else:
                    # Set the tax.amount to the correct amount
                    tax = r.tax_line_ids.filtered(lambda t: t.tax_id.id == c["tax_id"])
                    # Trigger write action only when necessary
                    if tax.amount != c["amount"]:
                        tax.amount = c["amount"]

        return res

    @api.multi
    def action_invoice_re_open(self):
        # If we are currently in a custom state, prevent the state from being written to "open"
        # also if no id is given skip the state from being overwritten (should have no effect anyways)
        if self.state != "sent" and self.id:
            return super().action_invoice_re_open()
        return

    def _set_global_discounts_by_tax(self):
        """Create invoice global discount lines by taxes combinations and
        discounts.
        """
        self.ensure_one()
        if not self.global_discount_ids:
            return
        invoice_global_discounts = self.env['account.invoice.global.discount']
        taxes_keys = {}
        ### Re-using another variable for tax calculation including the GD in invoices.
        taxes_keys2 = {}
        # Perform a sanity check for discarding cases that will lead to
        # incorrect data in discounts
        for inv_line in self.invoice_line_ids.filtered(
                lambda l: not l.display_type):
            ### Re-initializing. Else the next inv_line compares with the previous stored value throws exception.
            taxes_keys = {}
            if not inv_line.invoice_line_tax_ids:
                raise UserError(_(
                    "With global discounts, taxes in lines are required."
                ))
            for key in taxes_keys:
                if key == inv_line.invoice_line_tax_ids:
                    break
                elif key & inv_line.invoice_line_tax_ids:
                    raise UserError(_(
                        "Incompatible taxes found for global discounts."
                    ))
            else:
                taxes_keys[inv_line.invoice_line_tax_ids] = True
                taxes_keys2[inv_line.invoice_line_tax_ids] = True
        for tax_line in self.tax_line_ids:
            key = []
            to_create = True
            for key in taxes_keys2:
                if tax_line.tax_id in key:
                    to_create = taxes_keys2[key]
                    taxes_keys2[key] = False  # mark for not duplicating
                    break  # we leave in key variable the proper taxes value
            if not to_create:
                continue
            base = tax_line.base_before_global_discounts or tax_line.base
            for global_discount in self.global_discount_ids:
                discount = global_discount._get_global_discount_vals(base)
                invoice_global_discounts += invoice_global_discounts.new({
                    'name': global_discount.display_name,
                    'invoice_id': self.id,
                    'global_discount_id': global_discount.id,
                    'discount': global_discount.discount,
                    'base': base,
                    'base_discounted': discount['base_discounted'],
                    'account_id': global_discount.account_id.id,
                    'tax_ids': [(4, x.id) for x in key],
                })
                base = discount['base_discounted']
        self.invoice_global_discount_ids = invoice_global_discounts

    @api.multi
    def get_taxes_values(self):
        # Call super (should call function from catch weight module)
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        round_curr = self.currency_id.round
        # Loop through generated tax groups
        for key, tax_group in tax_grouped.items():
            if ("invoice_id" and "tax_id") not in tax_group:
                continue
            # Get relevant information
            invoice = self.env["account.invoice"].browse([tax_group["invoice_id"]])
            tax = self.env["account.tax"].browse([tax_group["tax_id"]])
            # Update the tax amount when global discounts are set, base should be calculated correctly by cw8 module for cw8 products
            total_global_discount = sum([disc.discount for disc in invoice.global_discount_ids])
            if total_global_discount > 0:
                # Calculate new tax, take global discounts into account
                tax_amount = tax_group["base"] * (1 - total_global_discount / 100) * (tax.amount / 100)
                tax_group["amount"] = round_curr(tax_amount)
        return tax_grouped
