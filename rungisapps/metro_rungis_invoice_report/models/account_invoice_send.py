from odoo import fields, models, api


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    data_to_transfert = fields.Boolean("data_to_transfert", compute='compute_booleans')
    to_transfert = fields.Boolean("to_transfert", compute='compute_booleans')

    @api.depends('invoice_ids.duplicate_watermark')
    def compute_booleans(self):
        for rec in self:
            if rec.invoice_ids.duplicate_watermark >= 1:
                rec.data_to_transfert = False
                rec.to_transfert = False
            else:
                rec.data_to_transfert = True
                rec.to_transfert = True
