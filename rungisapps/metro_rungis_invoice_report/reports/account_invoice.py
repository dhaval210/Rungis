from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    duplicate_watermark = fields.Integer(string="Duplicate watermark", default=False, copy=False)


class DuplicateWatermark(models.AbstractModel):
    _name = 'report.metro_rungis_invoice_report.print_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        account_invoice = self.env['account.invoice'].browse(docids)
        for rec in account_invoice:
            if rec.state == 'open':
                rec.duplicate_watermark = rec.duplicate_watermark + 1
        return {
            'docs': account_invoice,
        }


class AccountInvoiceGlobalDiscount(models.Model):
    _inherit = "account.invoice.global.discount"

    gross_amt = fields.Float(string='Gross amount', digits=dp.get_precision('Product Price'),
                             compute="compute_grossamt_amt_tot", readonly=True)
    amt_tot = fields.Float(string='Amount Tax', digits=dp.get_precision('Product Price'),
                           compute="compute_grossamt_amt_tot", readonly=True)

    def compute_grossamt_amt_tot(self):
        for rec in self:
            for tax_id in rec.tax_ids:
                for taxes in rec.invoice_id.tax_line_ids:
                    if tax_id.id == taxes.tax_id.id:
                        rec.amt_tot += taxes.amount + taxes.amount_rounding / 100
            rec.gross_amt = rec.amt_tot + rec.base_discounted

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    delivery_no = fields.Char(string="Lieferschein Nr.", compute="_compute_delivery_no_so_pos_no")
    so_pos_no = fields.Char(string="so position no", compute="_compute_delivery_no_so_pos_no")
    add_a_note = fields.Text(string="Add a note", Translate=True)

    @api.depends("sale_line_ids")
    def _compute_delivery_no_so_pos_no(self):
        for iline in self:
            delivery_notes = []
            so_position = []
            order_lines = self.env["sale.order.line"].search([
                ("order_id.name", "=", iline.origin),
                ("product_id", "=", iline.product_id.id),
                ("company_id", "=", iline.company_id.id),
            ])
            for oline in order_lines:
                if oline.delivery_no not in delivery_notes and oline.delivery_no:
                    delivery_notes.append(oline.delivery_no)
                    so_position = oline.so_pos_no
            iline.delivery_no = ", ".join(delivery_notes)
            iline.so_pos_no = so_position

