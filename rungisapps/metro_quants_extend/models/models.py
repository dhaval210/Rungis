# -*- coding: utf-8 -*-

from odoo import models, fields, api

class quants_extend(models.Model):
     _inherit = 'stock.quant'
     alert_date = fields.Datetime(related='lot_id.alert_date', store=True)
     use_date = fields.Datetime(related='lot_id.use_date', store=True)