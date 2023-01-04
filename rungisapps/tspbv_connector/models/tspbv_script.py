# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.



from odoo import fields, models


class TspbvScript(models.Model):
    _name = "tspbv.script"
    _description = 'TSPBV Script'
    _order = 'name'

    name = fields.Char('Name')
    code = fields.Text('Code')