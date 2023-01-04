# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    tour_ids = fields.One2many('tour.assignment', 'partner_id', 'Tour Assignment Info')
    calling_time = fields.Float('Anrufszeit')
    substitute_user_id = fields.Many2one('res.users', string='Vertretung',help='The substitute internal user in charge of this contact.')
