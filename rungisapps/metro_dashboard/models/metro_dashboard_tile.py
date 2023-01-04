# -*- coding: utf-8 -*-
import logging
import json

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class MetroDashboardTile(models.Model):
    _name = "metro.dashboard.tile"
    _description = "Tiles of the Metro Dashboard"
    _order = "sequence,id"

    name = fields.Char(
        string="Title",
        compute="_get_fields",
        required=True,
        store=True
    )
     
    goal_id = fields.Many2one(
        "gamification.goal",
        ondelete="set null"
    )
    statistic_id = fields.Many2one(
        "metro.dashboard.statistics",
        ondelete="cascade"
    )
    dashboard_id = fields.Many2one(
        "metro.dashboard",
        ondelete="cascade"
    )
    challenge_line_id = fields.Many2one(
        "gamification.challenge.line",
        ondelete="cascade"
    )
    line_ids = fields.One2many(
        "metro.dashboard.tile.line",
        "tile_id"
    )
    line_count = fields.Integer(
        compute="_get_line_count",
        store=True
    )
    insert_new_line = fields.Boolean(
        string="Insert newline after this tile",
        default=False
    )
    sequence = fields.Integer()

    user_ids = fields.One2many(
        "res.users",
        related="dashboard_id.user_ids"
    )
    use_linebreak = fields.Boolean(
        related="dashboard_id.use_linebreak"
    )
    api_available = fields.Boolean(
        string="Available in the API",
        description="If enabled this tile is accessible via the API."
    )
    double_width = fields.Boolean(
        string="Double tile size?",
        default=False
    )
    # Fields which are available in both the gamification.goal and the metro.dashboard.statistics models
    suffix = fields.Char(
        string="Suffix for values",
        compute="_get_fields"
    )
    use_timeframes = fields.Boolean(
        string="Use predefined timeframes",
        compute="_get_fields"
    )
    cust_timeframe = fields.Char(
        "Custom timeframe",
        compute="_get_fields"
    )
    result_short = fields.Char(
        compute="_get_short_results",
        store=True
    )
    result_short90 = fields.Char(
        compute="_get_short_results",
        store=True
    )

    # Gamification Goal specific fields
    current_progress = fields.Float(
        string="",
        related="goal_id.current",
        digits=(12,2)
    )
    current_progress90 = fields.Float(
        string="",
        related="goal_id.current90",
        digits=(12,2)
    )
    progress_difference = fields.Float(
        compute="get_difference"
    )
    progress_difference90 = fields.Float(
        compute="get_difference"
    )
    target = fields.Float(
        related="goal_id.target_goal"
    )
    goal_condition = fields.Selection(
        string="Display Mode",
        related="goal_id.definition_condition"
    )
    current_progress_int = fields.Integer(
        compute="_get_progress_int"
    )
    current_progress90_int = fields.Integer(
        compute="_get_progress_int"
    )
    missing_dependencies = fields.Char(
        related="goal_id.uninstalled_dependencies"
    )

    # Statistics specific fields
    result = fields.Char(
        related="statistic_id.value"
    )
    result90 = fields.Char(
        related="statistic_id.value90"
    )
    visualisation = fields.Selection(
        string="Visualisation Type",
        related="statistic_id.visualisation"
    )
    keys = fields.Char(
        related="statistic_id.keys",
        store=True
    )
    keys90 = fields.Char(
        related="statistic_id.keys90",
        store=True
    )
    monetary = fields.Boolean(
        related="statistic_id.monetary"
    )
    empty = fields.Boolean(
        related="statistic_id.empty"
    )
    empty90 = fields.Boolean(
        related="statistic_id.empty90"
    )
    # Needed for enabling the dashboard charts to have a suffix for each dataset (data_source = "data")
    data_source = fields.Selection(
        related="statistic_id.data_source"
    )

    @api.depends('current_progress')
    def get_difference(self):
        for recd in self:
            if recd.current_progress and recd.target and recd.current_progress90:
                recd.progress_difference = recd.current_progress - recd.target
                recd.progress_difference90 = recd.current_progress90 - recd.target

    @api.model
    def create(self, vals):
        res = super(MetroDashboardTile, self).create(vals)

        res.update_lines()
        
        return res
    
    @api.multi
    def write(self, vals):
        reference_changed = False
        # Check if the statistic id changed
        if "statistic_id" in vals or "goal_id" in vals:
            reference_changed = True
        # Update the current tile, this sets the new statistic id
        res = super(MetroDashboardTile, self).write(vals)
        if reference_changed:
            # Unlink all old metro.dashboard.tile.line's
            for line in self.line_ids:
                line.unlink()
            # Get the table data of the statistic
            # create lines for the default timeframe
            self.update_lines()
        return res

    @api.one
    def update_tile(self):
        if self.goal_id:
            self.goal_id.update_goal()
            if self.goal_id.challenge_id.display_one_tile:
                for line in self.line_ids:
                    line.update_goal()
            else:
                self.update_lines()
        elif self.statistic_id and self.statistic_id.data_source == "python":
            self.statistic_id.execute_code()
            self.update_lines()
        elif self.statistic_id and self.statistic_id.data_source == "data":
            self.statistic_id._extract_from_dataset()
        self._get_fields()

    # Updates the MetroDashboardTileLine's
    # alternative_timeframe : Whether the lines are calculated for timeframe 90 days or 30 days (only for use_timeframe = True)
    @api.multi
    def update_lines(self, alternative_timeframe = False):
        for rec in self:
            reference = None
            if rec.statistic_id:
                reference = rec.statistic_id
            elif rec.goal_id:
                reference = rec.goal_id
            # Load table data from database
            if not reference:
                return
            if not reference.table_data and alternative_timeframe == False:
                return
            if not reference.table_data90 and alternative_timeframe:
                return
            table_data = None
            if alternative_timeframe:
                table_data = json.loads(reference.table_data90)
            else:
                table_data = json.loads(reference.table_data)

            data = {}
            # Convert it to a form that is easier to work with
            # and shorten the data to not generate thousands of TileLines
            for d in table_data[:7]:
                label, val, suffix, sequence = self._get_table_data(d)
                data[label] = [val, suffix, sequence]
            if len(table_data) > 7 and table_data[7]["label"] == "More items:":
                label, val, suffix, sequence = self._get_table_data(table_data[7])
                data[label] = [val, suffix, sequence]
            elif len(table_data) > 7:
                diff = len(table_data) - 7
                data["More items:"] = [diff, "", 10]

            tile_lines = self.env["metro.dashboard.tile.line"].search([
                ("tile_id", "=", rec.id),
                ("default_timeframe", "=", False if alternative_timeframe else True)
            ])
            # Loop through lines
            for line in tile_lines:
                # Delete lines which are not in the data
                # dictionary anymore
                if not line.name in data:
                    line.unlink()
                    continue
                # Update existing values and delete it from the
                # data dictionary afterwards
                line.progress = data[line.name][0]
                line.target = data[line.name][0] + 1 if line.name != "More items:" else data[line.name][0]
                line.suffix   = data[line.name][1]
                line.sequence = data[line.name][2]
                del data[line.name]

            # Create leftover lines
            for d in data:
                self.env["metro.dashboard.tile.line"].create({
                    "name": d,
                    "progress": data[d][0],
                    "target": data[d][0] if d == "More items:" else data[d][0] + 1,
                    "suffix": data[d][1],
                    "sequence": data[d][2],
                    "tile_id": rec.id,
                    "default_timeframe": False if alternative_timeframe else True
                })
            # If the statistic uses multiple timeframes
            # also generate the table for the other timeframe
            if reference.use_timeframes and\
                reference.table_data90 and not alternative_timeframe:
                self.update_lines(True)

    def _get_table_data(self, data):
        label  = ""
        val    = 0
        suffix = ""
        sequence = -1
        if "label" in data:
            label = data["label"]
        if "value" in data:
            val = data["value"]
        if "suffix" in data:
            suffix = data["suffix"]
        if "sequence" in data:
            sequence = data["sequence"]
        return (label, val, suffix, sequence)

    @api.depends("line_ids")
    def _get_line_count(self):
        for r in self:
            r.line_count = len(r.line_ids)

    @api.depends("statistic_id", "goal_id")
    def _compute_use_timeframes(self):
        for r in self:
            if r.statistic_id:
                r.use_timeframes = r.statistic_id.use_timeframes
            elif r.goal_id:
                r.use_timeframes = r.goal_id.use_timeframes

    @api.depends("statistic_id", "goal_id")
    def _compute_custom_timeframe(self):
        for r in self:
            if r.statistic_id:
                r.cust_timeframe = r.statistic_id.cust_timeframe
            elif r.goal_id:
                r.cust_timeframe = r.goal_id.cust_timeframe

    @api.model
    def _cron_update(self):
        # Get statistics and goals which are linked to tiles
        goal_query = "SELECT goal_id FROM metro_dashboard_tile WHERE goal_id IS NOT NULL GROUP BY goal_id"
        statistic_query = "SELECT statistic_id FROM metro_dashboard_tile WHERE statistic_id IS NOT NULL GROUP BY statistic_id"
        tile_query = "SELECT id FROM metro_dashboard_tile WHERE statistic_id IS NOT NULL"
        # Delete tiles without any reference
        delete_query = "DELETE FROM metro_dashboard_tile WHERE statistic_id IS NULL AND goal_id IS NULL AND challenge_line_id IS NULL"

        # Execute query, select goal ids and remove duplicates with group by
        # So only get the goals which are linked to the tiles
        self.env.cr.execute(goal_query)
        goal_ids = self.env.cr.fetchall()

        self.env.cr.execute(statistic_query)
        statistic_ids = self.env.cr.fetchall()

        self.env.cr.execute(tile_query)
        tile_ids = self.env.cr.fetchall()

        self.env.cr.execute(delete_query)

        # Loop through the recordset of goal ids, get the object of it
        # and update it with the model function
        for goal in goal_ids:
            self.env["gamification.goal"].browse([goal[0]]).update_goal()
        
        for statistic in statistic_ids:
            self.env["metro.dashboard.statistics"].browse([statistic[0]]).update_value()
        
        for id in tile_ids:
            # _logger.info("Update Line: %s", id[0])
            self.env["metro.dashboard.tile"].browse([id[0]]).update_lines()

    # Reformat number if it is too big to display it on a tile
    @api.depends("result", "current_progress")
    def _get_short_results(self):
        for r in self:
            if r.visualisation == "number":
                r.result_short = self.number_shortening(r.result)
                r.result_short90 = self.number_shortening(r.result90)
            elif r.goal_id:
                r.result_short = self.number_shortening(r.current_progress)
                r.result_short90 = self.number_shortening(r.current_progress90)
    
    # Convert normal progress variable (float) to an integer
    @api.depends("current_progress")
    def _get_progress_int(self):
        for r in self:
            if r.current_progress:
                r.current_progress_int = round(r.current_progress)
            if r.current_progress90:
                r.current_progress90_int = round(r.current_progress90)

    @api.depends("goal_id", "statistic_id")
    def _get_fields(self):
        for rec in self:
            if rec.challenge_line_id:
                rec.name = rec.challenge_line_id.definition_id.name
                rec.use_timeframes = rec.challenge_line_id.definition_id.use_timeframes
                rec.cust_timeframe = rec.challenge_line_id.definition_id.cust_timeframe
                rec.suffix = rec.challenge_line_id.definition_id.suffix
            elif rec.statistic_id:
                rec.name = rec.statistic_id.name
                rec.use_timeframes = rec.statistic_id.use_timeframes
                rec.cust_timeframe = rec.statistic_id.cust_timeframe
                rec.suffix = rec.statistic_id.suffix
                if rec.monetary:
                    rec.statistic_id.symbol
            else:
                rec.suffix = None

    def number_shortening(self, number, decimals = 1):
        signs = ["k", "m", "b", "t", "q", "Q", "s", "S"]
        num = str(number).split(".")[0]
        negative = False

        if len(num) == 0:
            return

        # If the number is negative, store it for later and remove leading "-"
        if num[0] == "-":
            negative = True
            num = num[1:]
        for i in range(1, len(signs) + 1):
            if len(num) > (i * 3) and len(num) <= (i * 3 + 3):
                # Calculate indexes for cutting numbers at the right place
                first_cut = len(num) - (i*3)
                second_cut = first_cut + decimals

                # Get the decimals which will be appended to the short number
                num_decimals = num[first_cut:second_cut]
                # Get decimals of decimals, this is required for rounding the number correctly
                sub_decimals = num[second_cut:]
                # Add the numbers together and round them (sub_decimals will be removed in this step
                # but the number will be rounded the right way)
                dec = float(num_decimals+"."+sub_decimals)
                decimal = int(round(dec, 0))

                # Shorten number
                cut = i * 3

                # Add the decimals if they are unequal to 0
                if decimal == 0:
                    num = num[:-cut]
                elif decimal == 10:
                    num = str(int(num[:-cut]) + 1)
                else:
                    num = num[:-cut] + "." + str(decimal)
                
                # Add the sign
                num += signs[i - 1]
                break
        # Add - for negative values
        if negative:
            num = "-" + num
        return num

