from odoo import fields, models


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_inventory_master = fields.Boolean(
        "Inventory Master",
        implied_group='metro_procurement_manager.group_inventory_master'
    )

    whin_is_done = fields.Boolean(
        string='WH-IN Done',
        default=False,
        config_parameter='metro_procurement_manager.whin_is_done'
    )
