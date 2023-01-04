from odoo import fields, models


class AutoValidationSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Auto Validation Settings'

    auto_validate_picking = fields.Boolean(
        string='Auto validate Picking',
        default=False,
        config_parameter='metro_auto_validate_operation_type.auto_validate_picking'
    )

    assign_picking_filter_id = fields.Many2one(
        'ir.filters',
        string='Create Picking Filter',
        config_parameter='metro_auto_validate_operation_type.assign_picking_filter_id',
        readonly=False
    )
