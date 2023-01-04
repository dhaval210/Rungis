# -*- coding: utf-8 -*-
import logging
import json

from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MetroDashboard(models.Model):
    _name = "metro.dashboard"
    _description = "Metro Dashboards"

    name = fields.Char(
        string="Name of the Dashboard",
        required=True
    )
    user_ids = fields.One2many(
        "res.users",
        "dashboard_id",
        string="Assignees"
    )
    tile_ids = fields.One2many(
        "metro.dashboard.tile",
        "dashboard_id"
    )
    challenge_ids = fields.Many2many(
        "gamification.challenge",
        string="Challenges"
    )
    statistic_ids = fields.Many2many(
        "metro.dashboard.statistics",
        string="Statistics"
    )
    use_linebreak = fields.Boolean(
        string="Whether linebreaks are used on tiles of this dashboard or not",
        compute="_compute_linebreak"
    )
    api_available = fields.Boolean(
        string="Available in the API",
        description="If this field is enabled the full dashboard will be available in the API (/metro_dashboard/api/dashboard/). Single tiles corresponding to the dashboard are not necessarily available in the API (/metro_dashboard/api/tile/)",
        default=False
    )

    # When a new dashboard gets created this function will be called
    @api.model
    def create(self, vals):
        res = super(MetroDashboard, self).create(vals)
        # Loop through ids of challenges which were chosen in the challenge_ids field
        sequence = 0
        if "challenge_ids" in vals:
            for challenge_id in vals["challenge_ids"][0][2]:
                challenge = self.env["gamification.challenge"].browse([challenge_id])
                # Create DashboardTile with the current ChallengeLine and the ID this record will have
                if challenge.display_one_tile:
                    self._create_tile_with_table(challenge=challenge, id=res.id, sequence=sequence)
                    sequence += 1
                else:
                    for i in range(0, len(challenge.line_ids)):
                        line = challenge.line_ids[i]
                        self._create_tile(obj=line, id=res.id, sequence=sequence)
                        sequence += 1
        if "statistic_ids" in vals:
            for statistic_id in vals["statistic_ids"][0][2]:
                statistic = self.env["metro.dashboard.statistics"].browse([statistic_id])
                self._create_tile(obj=statistic, id=res.id, is_goal=False, sequence=sequence)
                sequence += 1

        return res

    # When a dashboard gets edited this function will get called
    @api.multi
    def write(self, vals):
        res = super(MetroDashboard, self).write(vals)

        query = "SELECT sequence FROM metro_dashboard_tile WHERE dashboard_id=%s AND sequence IS NOT NULL ORDER BY sequence DESC LIMIT 1"
        self.env.cr.execute(query, [self.id])
        sequence = self.env.cr.fetchone()

        if sequence:
            sequence = sequence[0] + 1
        else:
            sequence = 0

        # Do that only if the user changed the corresponding challenges to the dashboard
        if "challenge_ids" in vals:
            # If the new list of challenges is empty
            # Delete all tiles with a goal assigned to it
            if len(self.challenge_ids) == 0:
                tiles = self.env["metro.dashboard.tile"].search([
                    ("dashboard_id", "=", self.id),
                    ("challenge_line_id", "!=", None)
                ])
                for tile in tiles:
                    self._remove_tile(tile)
            # If the challenges aren't empty, manage them
            else:
                lines = []
                already_created_ids = []
                # Getting the challenge_line_ids and names corresponding to the challenge
                for challenge in self.challenge_ids:
                    if challenge.display_one_tile:
                        tile_id, line_id = self._create_tile_with_table(challenge=challenge, sequence=sequence)
                        already_created_ids.append(tile_id)
                        lines.append(line_id)
                        sequence += 1
                    else:
                        for line in challenge.line_ids:
                            lines.append(line)

                # Check existing tiles if they need to be removed or can stay
                for tile in self.tile_ids:
                    # Remove if line is None and do nothing if line is an object
                    line = self._check_existing_tile(tile, lines)
                    if tile.goal_id:
                        if line == None or tile.id not in already_created_ids:
                            self._remove_tile(tile)
                        else:
                            lines.remove(line)
                
                # Creating leftover tiles
                for i in range(0, len(lines)):
                    line = lines[i]
                    self._create_tile(obj=line, sequence=sequence)
                    sequence += 1
        
        if "statistic_ids" in vals:
            # Remove all Tiles which are linked to a statistic
            if len(self.statistic_ids) == 0:
                tiles = self.env["metro.dashboard.tile"].search([
                    ("dashboard_id", "=", self.id),
                    ("statistic_id", "!=", None)
                ])
                for tile in tiles:
                    self._remove_tile(tile)
            else:
                # Get all ids of the linked statistics
                ids = [s.id for s in self.statistic_ids]
                # Get tiles which have no goal_id, correspond to the dashboard
                # and where their id is not in the ids variable
                remove_tiles = self.env["metro.dashboard.tile"].search([
                    ("dashboard_id", "=", self.id),
                    ("statistic_id", "not in", ids),
                    ("goal_id", "=", None),
                ])

                # Remove all tiles which are not linked
                # to the dashboard anymore
                for t in remove_tiles:
                    self._remove_tile(t)
                
                # Remove ids of tiles which already exist
                for tile in self.tile_ids:
                    if tile.statistic_id:
                        ids.remove(tile.statistic_id.id)
                
                # Create tiles
                for id in ids:
                    statistic = self.env["metro.dashboard.statistics"].browse([id])
                    self._create_tile(obj=statistic, is_goal=False, sequence=sequence)
                    sequence += 1

        query = "SELECT sequence FROM metro_dashboard_tile WHERE dashboard_id=%s AND sequence IS NOT NULL ORDER BY sequence ASC LIMIT 1;"
        self.env.cr.execute(query, [self.id])
        lowest_sequence = self.env.cr.fetchone()

        if not lowest_sequence:
            return res
        
        lowest_sequence = lowest_sequence[0]

        if lowest_sequence != 0:
            for tile in self.tile_ids:
                tile.sequence = tile.sequence - lowest_sequence
        
        return res

    @api.depends("tile_ids")
    def _compute_linebreak(self):
        for r in self:
            r.use_linebreak = False
            for t in r.tile_ids:
                if t.insert_new_line:
                    r.use_linebreak = True
                    break

    # Returns None when the Tile should be removed
    # Returns the gamification.challenge.line if the Tile should stay
    def _check_existing_tile(self, tile, lines):
        tile_id = tile.challenge_line_id.id

        # Should be more or less similar in performance than "if not in" or "if in" state
        # if tile.name not in lines["names"] and tile_id not in lines["ids"]:
        for line in lines:
            name = line.definition_id.name
            # Basically do nothing
            if tile.name == name and tile_id == line.id:
                return line

        return None

    # Checks if the users assigned to this dashboard are already assigned to another dashboard
    @api.multi
    @api.onchange("user_ids")
    def _check_reassignment(self):
        reassigned = []
        # Loop through the users assigned to the dashboard
        for user in self.user_ids:
            # Get the old dashboard id of current user
            query = "SELECT dashboard_id FROM res_users WHERE id=%s"
            self.env.cr.execute(query, [user.id])
            old_dashboard_id = self.env.cr.fetchone()[0]

            # Check if the user was assigned to a dashboard before and
            # if the current dashboard id is different from the old one
            if self._origin.id != old_dashboard_id and old_dashboard_id != None:
                info = {
                    "name": user.name,
                    "dashboard": self.env["metro.dashboard"].browse([old_dashboard_id]).name
                }
                reassigned.append(info)

        # Raise an error when at least one user is already assigned to another dashboard
        if len(reassigned) > 0:
            msg = "There is at least one user which is already assigned to another dashboard. "
            msg += "Please remove the user(s) from the dashboard(s) first.\nHere is a list of the users:\n\n"
            for user in reassigned:
                msg += "* "+ user["name"] + " ("+ user["dashboard"] +")\n"
            
            raise UserError(msg)

    # Creates tile with the given gamification.challenge.line record and optionally an ID
    # The function is_goal says if the current obj is a ChallengeLine or Statistics Object
    def _create_tile(self, obj, id=None, is_goal=True, sequence=0):
        DashboardTile = self.env["metro.dashboard.tile"]
        Goal = self.env["gamification.goal"]
        rec = {}

        if is_goal:
            rec = DashboardTile.create({
                "name": obj.name,
                "goal_id": Goal.search([("challenge_id", "=", obj.challenge_id.id), ("line_id", "=", obj.id)], limit=1).id,
                "dashboard_id": id if id is not None else self.id,
                "challenge_line_id": obj.id,
                "insert_new_line": False,
                "sequence": sequence,
            })
        else:
            double_width = False
            
            if not obj.visualisation == "number" and obj.keys:
                keys   = []
                keys90 = []
                if obj.keys:
                    keys = [key.strip() for key in obj.keys.split("\\s")]
                if obj.keys90:
                    keys90 = [key.strip() for key in obj.keys90.split("\\s")]
                if len(keys) >= 8 or len(keys90) >= 8:
                    double_width = True
            
            rec = DashboardTile.create({
                "name": obj.name,
                "statistic_id": obj.id,
                "dashboard_id": id if id is not None else self.id,
                "insert_new_line": False,
                "double_width": double_width,
                "sequence": sequence,
            })
        return rec.id

    def _create_tile_with_table(self, challenge, id=None, sequence=0):
        TableLine = self.env["metro.dashboard.tile.line"]
        Goal = self.env["gamification.goal"]
        tile_id = 0
        line_id = 0
        for i in range(0, len(challenge.line_ids)):
            curr_line = challenge.line_ids[i]
            if i == 0:
                tile_id = self._create_tile(obj=curr_line, id=id, sequence=sequence)
                line_id = curr_line
            else:
                TableLine.create({
                    "name": curr_line.name,
                    "tile_id": tile_id,
                    "challenge_line_id": curr_line.id,
                    "goal_id": Goal.search([
                        ("challenge_id", "=", challenge.id),
                        ("line_id", "=", curr_line.id),
                    ], limit=1).id
                })
        return (tile_id, line_id)

    def _remove_tile(self, tile = None):
        if not tile:
            return
        tile.unlink()
        return
