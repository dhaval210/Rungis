# -*- coding: utf-8 -*-

from odoo import fields, models

class TransporterRoute(models.Model):
    _name = 'transporter.route'

    name = fields.Char(
        string='Name',
        required=True,
    )
    transporter_id = fields.Many2one(
        'res.partner',
        string='Transporter',
        required=True,
    )
    route_line_ids = fields.One2many(
        'transporter.route.line',
        'route_id',
        string='Transporter Route Line',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
