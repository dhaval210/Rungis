from odoo import fields, models


class TspbvSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Tspbv Settings'

    async_pick = fields.Boolean(
        string='Async Picking Validation',
        default=False,
        config_parameter='tspbv_connector.async_pick'
    )
