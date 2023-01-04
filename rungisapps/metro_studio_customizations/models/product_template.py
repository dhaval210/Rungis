# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_launch_date = fields.Date(
        string="Launch Date"
    )
