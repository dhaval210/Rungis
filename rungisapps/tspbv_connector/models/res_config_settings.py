from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class TspbvSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Tspbv Settings'

    assign_picking_filter_id = fields.Many2one(
        'ir.filters',
        string='Create Picking Filter',
        config_parameter='tspbv_connector.assign_picking_filter_id',
        readonly=False
    )
    assign_batch_picking_filter_id = fields.Many2one(
        'ir.filters',
        string='Create Batch Picking Filter',
        config_parameter='tspbv_connector.assign_batch_picking_filter_id',
        readonly=False
    )
    # add retries
    # add allow/denie backorder
    backorder = fields.Boolean(
        string='Allow Backorder',
        default=False,
        config_parameter='tspbv_connector.allow_backorder'
    )
