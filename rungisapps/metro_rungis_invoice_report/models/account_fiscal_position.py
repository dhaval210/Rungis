from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    invoice_information = fields.Text(string="Invoice Information", translate=True)
