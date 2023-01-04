# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cw_quantity = fields.Float(string='CW Quantity')
    product_cw_uom_id = fields.Many2one('uom.uom', string='CW Unit of Measure')
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
