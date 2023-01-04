# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

def build_tile_lines_list(rec):
    lines = []
    for line in rec:
        # Build dictionary which will be appended to the tile later
        curr_line = {}
        curr_line["name"] = line.name
        curr_line["reached"] = False
        
        if line.goal_id:
            curr_line["progress"] = line.goal_progress
            curr_line["target"] = line.goal_target
            curr_line["suffix"] = line.goal_suffix
            if line.goal_progress >= line.goal_target:
                curr_line["reached"] = True
        else:
            curr_line["progress"] = line.progress
            curr_line["target"] = line.target
            curr_line["suffix"] = line.suffix
            if line.progress >= line.target:
                curr_line["reached"] = True

        lines.append(curr_line)
    return lines


def generate_tile_data(tile):
    table_lines = request.env["metro.dashboard.tile.line"].search([
        ("tile_id", "=", tile.id),
        ("default_timeframe", "=", True),
    ])
    table_lines90 = request.env["metro.dashboard.tile.line"].search([
        ("tile_id", "=", tile.id),
        ("default_timeframe", "=", False),
    ])

    # Get the structure needed for building the table
    table = {}
    table["30"] = build_tile_lines_list(table_lines)
    table["90"] = build_tile_lines_list(table_lines90)

    t = {
        "id": tile.id,
        "name": tile.name,
        "suffix": tile.suffix,
        "table": table,
        "linebreak": False,
        "double_width": tile.double_width,
        "keys": tile.keys,
        "keys90": tile.keys90,
        "use_timeframes": tile.use_timeframes,
        "cust_timeframe": tile.cust_timeframe,
        "result_short": tile.result_short,
        "result_short90": tile.result_short90,
        "has_statistic": False,
        "has_goal": False,
        "has_ch_line": False,
    }

    if tile.challenge_line_id:
        t["has_ch_line"] = True
        if tile.goal_id:
            t["progress"] = tile.current_progress or 0.0
            t["progress90"] = tile.current_progress90 or 0.0
            t["target"] = tile.target or 0
            t["condition"] = tile.goal_condition
            t["progress_int"] = int(tile.current_progress or 0.0)
            t["progress90_int"] = int(tile.current_progress90 or 0.0)
            t["has_goal"] = True
    elif tile.statistic_id:
        t["result"] = tile.result
        t["result90"] = tile.result90
        t["visualisation"] = tile.visualisation
        t["empty"] = tile.empty
        t["empty90"] = tile.empty90
        t["has_statistic"] = True
    
    return t

class MetroDashboardApi(http.Controller):
    @http.route("/metro_dashboard/api/tile/<int:tile_id>", auth="none")
    def api_tile(self, tile_id, *args, **kw):
        if "db" in kw and request.session.db is not kw["db"]:
            request.session.db = kw["db"]

        # Get data from database
        tile = request.env["metro.dashboard.tile"].sudo().browse([tile_id])
        if not tile.exists():
            err = "The tile you've requested was not found."
            return http.request.render("metro_dashboard.dashboard_tile_api_page", {"error": err})
        if not tile.api_available:
            err = "Unfortunately the tile you've requested is not available in the API."
            return http.request.render("metro_dashboard.dashboard_tile_api_page", {"error": err})

        t = generate_tile_data(tile)

        return http.request.render("metro_dashboard.dashboard_tile_api_page", t)

    @http.route("/metro_dashboard/api/dashboard/<int:dashboard_id>", auth="none")
    def api_dashboard(self, dashboard_id, *args, **kw):
        if "db" in kw and request.session.db is not kw["db"]:
            request.session.db = kw["db"]
        
        d = request.env["metro.dashboard"].browse([dashboard_id])
        
        if not d.exists() or not d.api_available:
            err = "Unfortunately the dashboard you've requested is not available in the API or does not exist."
            return http.request.render("metro_dashboard.dashboard_api_page", {"error": err})
        
        tiles = request.env["metro.dashboard.tile"].sudo().search([\
            ("dashboard_id", "=", d.id),\
        ])
        dashboard = []
        for tile in tiles:
            t = generate_tile_data(tile)
            
            dashboard.append(t)

        return http.request.render("metro_dashboard.dashboard_api_page", {"dashboard": dashboard})

    @http.route("/metro_dashboard/get_db_name", auth="public", type="json")
    def get_db_name(self):
        db_name = request.session.db
        return {"db": db_name}
