from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class TspbvSession(models.Model):
    _name = 'tspbv.session'
    _description = 'Session Data for Pick by Voice'

    user_id = fields.Many2one(comodel_name='res.users', string='User')
    model_id = fields.Many2one(comodel_name='ir.model', string='Model')
    model_res_id = fields.Integer(string='Record ID')
    current_dialoglist_id = fields.Many2one(
        comodel_name='tspbv.dialoglist',
        string='Current Dialoglist'
    )
    current_line_ids = fields.One2many(
        comodel_name='stock.move.line',
        inverse_name='session_id',
        string='Current Lines'
    )
    current_item_id = fields.Many2one(
        comodel_name='stock.move.line',
        string='Current Item'
    )
    current_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Current Location'
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination Location'
    )
    picking_retries = fields.Integer(
        string='Retries',
        default=0
    )
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='session_id',
        string='Pickings'
    )

    _sql_constraints = [('user_id_unique', 'unique(user_id)',
                        'There can only be one session for an user')]
