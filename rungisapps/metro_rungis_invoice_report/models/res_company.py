from odoo import api, fields, models


class Compny(models.Model):
    _inherit = 'res.company'

    header_p1 = fields.Html(string="Header Seite 1")
    header_p2 = fields.Html(string="Header Seite 2")
    footer_p1 = fields.Html(string="Footer Seite 1")
    footer_p2 = fields.Html(string="Footer Seite 2")
    invoice_credit_payment = fields.Text(string="Invoice:credit payment", translate=True)
    invoice_final_text_box = fields.Text(string="Invoice:Final Text Box", translate=True)
    metro_bio_certificate = fields.Char(string="Bio Certificate", translate=True)