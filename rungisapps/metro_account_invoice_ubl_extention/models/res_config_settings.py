from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ubl_use_softm_delivery_note = fields.Boolean(
        string="Use data for delivery notes from softm interface",
        help="Use data for Delivery Notes from the softm interface instead from odoo",
        related="company_id.ubl_use_softm_delivery_note",
        readonly=False
    )
