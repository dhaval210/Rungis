# -*- coding: utf-8 -*-
from odoo import models, api, fields


class User(models.Model):
    _inherit = "res.users"

    dashboard_id = fields.Many2one(
        "metro.dashboard",
        ondelete="set null",
        string="Dashboard"
    )
