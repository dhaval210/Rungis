
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    def _get_refund(self, inv, mode):
        res = super(AccountInvoiceRefund, self)._get_refund(inv, mode)
        res.global_discount_ids = [(6, 0, inv.global_discount_ids.ids)]
        res._set_global_discounts_by_tax()
        return res



