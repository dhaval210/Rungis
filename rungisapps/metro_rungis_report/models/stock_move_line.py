# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    batch_id = fields.Many2one(comodel_name='stock.picking.batch')
