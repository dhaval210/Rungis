import logging

from odoo import api, fields, models, _
from datetime import timedelta, datetime


class ResCompany(models.Model):
    _inherit = "res.company"

    run_invoice_robot = fields.Boolean("Run invoice robot for this company", default=False)
