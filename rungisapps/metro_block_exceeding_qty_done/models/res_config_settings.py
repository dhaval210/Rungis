from odoo import fields, models


class AutoValidationSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Auto Validation Settings'

    block_exceeding_qty = fields.Boolean(
        string='Block exceeding Qty',
        default=False,
        config_parameter='metro_block_exceeding_qty_done.block_exceeding_qty'
    )

    block_qty_filter_id = fields.Many2one(
        'ir.filters',
        string='Picking Filter',
        config_parameter='metro_block_exceeding_qty_done.block_qty_filter_id',
        readonly=False
    )
