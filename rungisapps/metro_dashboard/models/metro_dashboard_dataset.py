# -*- coding: utf-8 -*-
import logging
import json

from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class MetroDashboardDataset(models.Model):
    _name = "metro.dashboard.dataset"
    _description = "A set of data."

    name = fields.Char(
        required=True
    )
    line_ids = fields.One2many(
        "metro.dashboard.dataset.line",
        "set_id"
    )
    line_count = fields.Integer(
        string="Size of dataset",
        compute="_get_line_count"
    )
    suffix = fields.Char()

    has_suffix = fields.Boolean(
        compute="_check_suffix_length"
    )

    keys = fields.Char(
        help="Keys used by the dataset, keys are the labels of your DataLines.",
        compute="_get_keys",
        store=True
    )

    @api.depends("line_ids")
    def _get_line_count(self):
        for r in self:
            r.line_count = len(r.line_ids)

    @api.depends("line_ids")
    def _get_keys(self):
        for r in self:
            r.keys = ""
            for i in range(0, r.line_count):
                r.keys += r.line_ids[i].name
                if not i == r.line_count - 1:
                    r.keys += " \\s "
        
    @api.depends("suffix")
    def _check_suffix_length(self):
        for r in self:
            suffix = r.suffix if r.suffix else ""
            if len(suffix) > 0:
                r.has_suffix = True
                continue
            r.has_suffix = False


class MetroDashboardDatasetLine(models.Model):
    _name = "metro.dashboard.dataset.line"
    _description = "A piece of data."
    _order = "sequence,id"

    sequence = fields.Integer()
    name = fields.Char(
        string="Label",
        required=True
    )
    set_id = fields.Many2one(
        "metro.dashboard.dataset",
        string="Dataset"
    )
    suffix = fields.Char(
        related="set_id.suffix"
    )
    value = fields.Float()
