# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, fields, api
import ast


class ResConfigSettings(models.TransientModel):
    """inherit inventory config and add two booleans"""
    _inherit = 'res.config.settings'

    cw_product_highlight = fields.Boolean(
        string='Cw Product Highlight',
        related="company_id.cw_product_highlight",
        readonly=False,
        store=False
    )
    operation_filters = fields.Many2many(
        comodel_name='stock.picking.type',
        string='Picking/Operation Type',
        related="company_id.operation_filters",
        readonly=False,
        store=False
    )
