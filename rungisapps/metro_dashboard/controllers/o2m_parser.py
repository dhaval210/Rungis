# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def buildTableLinesFromRecord(rec):
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


class O2mParser(http.Controller):

    @http.route("/web/metro_dashboard/get_table_lines/<model('metro.dashboard.tile'):tile>", type="json", auth="public")
    def get_table_lines(self, tile):
        # Get TableLines which are part of the dashboard
        table_lines = request.env["metro.dashboard.tile.line"].search([
            ("tile_id", "=", tile.id),
            ("default_timeframe", "=", True),
        ])
        table_lines90 = request.env["metro.dashboard.tile.line"].search([
            ("tile_id", "=", tile.id),
            ("default_timeframe", "=", False),
        ])
        lang = request.env.lang
        lang_id = request.env['res.lang'].search([('code', '=', lang)])
        # Variable which contains the formatted table_lines objects
        currency = request.env.user.company_id.currency_id
        fmt = "%.{0}f".format(currency.decimal_places)
        table = {}
        lines = buildTableLinesFromRecord(table_lines)
        for line in lines:
            line['progress'] = lang_id.format(fmt, line['progress'], grouping=True, monetary=True)
        table["30"] = lines

        lines = buildTableLinesFromRecord(table_lines90)
        table["90"] = lines

        return table

