# -*- coding: utf-8 -*-
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class MetroDashboardTileLine(models.Model):
    _name = "metro.dashboard.tile.line"
    _description = "Table Item of a Tile from the Metro Dashboard"
    _order = "sequence,id"

    name = fields.Char(
        required=True
    )
    progress = fields.Float(
        string="Current Progress"
    )
    target = fields.Float(
        string="Target/Max Value"
    )
    suffix = fields.Char()
    tile_id = fields.Many2one(
        "metro.dashboard.tile",
        string="Corresponding Tile",
        ondelete="cascade"
    )
    default_timeframe = fields.Boolean(
        string="Whether this object corresponds to the default timeframe",
        help="The default timeframe is either 30 days if use_timeframe is true, otherwise it's the timeframe used by this Statistic",
        default=True
    )
    goal_id = fields.Many2one(
        "gamification.goal"
    )
    goal_progress = fields.Float(
        string="Progress of the goal",
        related="goal_id.current"
    )
    goal_target = fields.Float(
        string="Target of the goal",
        related="goal_id.target_goal"
    )
    goal_suffix = fields.Char(
        string="Suffix",
        related="goal_id.definition_suffix"
    )
    challenge_line_id = fields.Many2one(
        "gamification.challenge.line"
    )
    sequence = fields.Integer()

    @api.one
    def update_goal(self):
        if not self.goal_id:
            return
        self.goal_id.update_goal()
