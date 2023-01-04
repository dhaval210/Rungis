from odoo import api, fields, models

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    delivery_no = fields.Char(string="Lieferschein Nr.", compute="_compute_delivery_no")


    @api.depends("sale_line_ids")
    def _compute_delivery_no(self):
        for iline in self:
            delivery_notes = []
            order_lines = self.env["sale.order.line"].search([
                ("order_id.name", "=", iline.origin),
                ("product_id", "=", iline.product_id.id),
                ("company_id", "=", iline.company_id.id),
            ])
            for oline in order_lines:
                if oline.delivery_no not in delivery_notes and oline.delivery_no:
                    delivery_notes.append(oline.delivery_no)
            iline.delivery_no = ", ".join(delivery_notes)
