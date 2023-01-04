# -*- coding: utf-8 -*-

from odoo import fields, models


class TransporterRoute(models.Model):
    _inherit = 'transporter.route'

    partner_id = fields.Many2one('res.partner', 'Partner')
    street = fields.Char(related="partner_id.street")
    city = fields.Char(related="partner_id.city")
    country_id = fields.Many2one(related="partner_id.country_id")
