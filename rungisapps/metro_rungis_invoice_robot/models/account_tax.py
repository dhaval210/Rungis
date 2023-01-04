from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = "account.tax"

    is_fake = fields.Boolean(
        string="Fake VAT",
        default=False,
        help="Identifies taxes as fake which will lead to an error prone invoice when generated & checked by the robot."
    )
