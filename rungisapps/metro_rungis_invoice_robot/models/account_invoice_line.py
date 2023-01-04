from odoo import models, api, _, fields
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    add_a_note = fields.Text(string="Add a note", Translate=True, copy=True)

    @api.multi
    def unlink(self):
        if self.filtered(lambda r: r.invoice_id and r.invoice_id.state not in ("draft", "sent")):
            raise UserError(_("You can only delete an invoice line if the invoice is in either draft or sent state."))
        return models.Model.unlink(self)
