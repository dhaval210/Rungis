# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Challenge(models.Model):
    _inherit = "gamification.challenge"

    display_one_tile = fields.Boolean(string="Display Challenge on one Tile", default=False)

    def _update_all(self):
        res = super(Challenge, self)._update_all()

        ch_lines = []

        # Find challenge lines which are part of the challenge
        for id in self.ids:
            lines = self.env["gamification.challenge.line"].search([
                ("challenge_id", "=", id)
            ])
            ch_lines.append(lines)

        # Loop through challenge lines
        for lines in ch_lines:
            for line in lines:
                # Get the goal which corresponds to the current line
                goal = self.env["gamification.goal"].search([
                    ("line_id", "=", line.id),
                    # ("challenge_id", "=", self.id)
                ], limit=1)
                # Get all tiles which are linked to the current line
                tiles = self.env["metro.dashboard.tile"].search([
                    ("challenge_line_id", "=", line.id)
                ])
                # Rereference the Many2one goal field of DashboardTile with the new goal id
                for tile in tiles:
                    tile.goal_id = goal.id
                # Get all DashboardTileLine's which are linked to the current line
                tile_lines = self.env["metro.dashboard.tile.line"].search([
                    ("challenge_line_id", "=", line.id)
                ])
                # Rereference the new goal id with the DashboardTileLine
                for tile_line in tile_lines:
                    tile_line.goal_id = goal.id

        return res