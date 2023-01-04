# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _


class PartnerFamily(models.Model):
    _name = 'partner.family'
    _description = 'Partner Family'

    name = fields.Char(string='Customer Family', required=True)

    _sql_constraints = [
       ('name_unique', 'UNIQUE(name)',
        "The Partner family name must be unique"),
    ]


class Partner(models.Model):
    _inherit = 'res.partner'

    partner_family_id = fields.Many2one('partner.family', string='Customer Family')
