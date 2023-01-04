from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()

        for so in self:
            if so.partner_id:
                invoice_partner = self.env["res.partner"].search([
                    ("parent_id", "=", so.partner_id.id),
                    ("type", "=", "invoice"),
                    ("is_company", "=", True)
                ])
                if invoice_partner:
                    so.update({
                        "partner_invoice_id": invoice_partner.id,
                    })
