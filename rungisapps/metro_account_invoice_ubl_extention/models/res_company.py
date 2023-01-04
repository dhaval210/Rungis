from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    ubl_use_softm_delivery_note = fields.Boolean(
        string="Use data for delivery notes from softm interface",
        help="Use data for Delivery Notes from the softm interface instead from odoo",
        default=False
    )
