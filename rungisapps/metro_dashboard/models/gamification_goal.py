# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
import time
import logging
import json
import psycopg2

from odoo import api, fields, models
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class GoalDefinition(models.Model):
    _inherit = "gamification.goal.definition"

    use_timeframes = fields.Boolean(
        string="Use predefined timeframes",
        help="If activated the goal will be calculated for the last 30 and last 90 days. Note: Only if computation_mode=='python'.",
        default=True
    )
    cust_timeframe = fields.Char(
        "Custom Timeframe",
        help="This label is shown when a timeframe does not use the standard timeframes (use_timeframes=True)"
    )
    dependencies = fields.Char(
        string="All dependencies",
        help="A list of modules which need to be installed before calculating the value."
    )

class Goal(models.Model):
    _inherit = "gamification.goal"

    use_timeframes = fields.Boolean(
        string="Use predefined timeframes",
        related="definition_id.use_timeframes"
    )
    cust_timeframe = fields.Char(
        related="definition_id.cust_timeframe",
        store=True
    )
    last_day = fields.Date(
        "Last day for calculating the value",
        default=fields.Date.to_string(datetime.now().date() + timedelta(days=1))
    )
    first_day = fields.Date(
        "First day for calculating the value"
    )
    current90 = fields.Float("Current Value", help="Current value for the last 90 days", default=0)
    tile_ids = fields.One2many(
        "metro.dashboard.tile",
        "goal_id"
    )
    dashboard_ids = fields.One2many(
        "metro.dashboard",
        compute="_get_dashboard_ids"
    )
    table_data = fields.Char(
        help="The data for your table"
    )
    table_data90 = fields.Char(
        string="Table data for the last 90 days",
        help="The data which gets displayed in the table for the timeframe 'Last 90 days'."
    )
    uninstalled_dependencies = fields.Char(
        help="Please install those modules before calculating the value of this goal."
    )

    @api.multi
    def update_goal(self):
        for r in self:
            if r.computation_mode == "python":
                # Compute code and extract variables
                r.execute_code()
                # if self.env.context.get("commit_gamification"):
                #     self.env.cr.commit()
            else:
                super(Goal, r).update_goal()
        
        return True

    @api.one
    def execute_code(self, days90 = False):
        self.check_dependencies()
        if self.uninstalled_dependencies:
            _logger.warn("Please install the following dependencies before calculting %s: %s", self.definition_id.name, self.uninstalled_dependencies)
            self.current = 0
            self.current90 = 0
            return
        self.last_day = datetime.now().date() + timedelta(days=1)
        self.first_day = self.last_day - timedelta(days=31)
        if days90:
            self.first_day -= timedelta(days=60)
        ctx = {
            #"val": self.val,
            "object": self,
            "env": self.env,
            "datetime": datetime,
            "timedelta": timedelta,
            "time": time,
            "date": date,
            "type": type,
            "sorted": sorted,
            "variable": self.env["metro.dashboard.variable"],
            "log": _logger.info,
            "load": json.loads,
            "parse": json.dumps,
        }
        code = self.definition_id.compute_code.strip()
        safe_eval(code, ctx, mode="exec", nocopy=True)
        
        res = ctx.get("result")
        table = []
        
        if res is not None and isinstance(res, (float, pycompat.integer_types)):
            if days90:
                self.current90 = res
            else:
                self.current = res
        else:
            _logger.error("Please make sure that the result variable in %s is from the type number (current: %s)", self.definition_id.name, type(res))
        
        if ctx.get("table"):
            table = json.dumps(ctx.get("table"))
            if days90:
                self.table_data90 = table
            else:
                self.table_data = table
        
        if self.use_timeframes and not days90:
            self.execute_code(True)

    @api.multi
    def _get_dashboard_ids(self):
        for r in self:
            dashboard_ids = []
            for tile in r.tile_ids:
                if not tile.dashboard_id in dashboard_ids:
                    dashboard_ids.append(tile.dashboard_id)
            r.dashboard_ids = dashboard_ids

    @api.multi
    def check_dependencies(self):
        for r in self:
            if r.definition_id.dependencies:
                r.uninstalled_dependencies = ""
                dependencies = r.definition_id.dependencies.split(",")
                for i in range(len(dependencies)):
                    dependency = dependencies[i]
                    module = self.env["ir.module.module"].search([("name", "=", dependency)])
                    if module.state != "installed":
                        r.uninstalled_dependencies += dependency + ","
                # Remove trailing comma and set to inactive if dependencies are not installed
                if r.uninstalled_dependencies:
                    r.uninstalled_dependencies = r.uninstalled_dependencies[:-1]
