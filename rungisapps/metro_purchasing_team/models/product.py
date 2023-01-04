# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PurchasingTeam(models.Model):
    _name = "purchasing.team"
    _description = "Purchasing Team"

    name = fields.Char('Name', required=True)

class ProductCategory(models.Model):
    _inherit = "product.category"

    purchasing_team_id = fields.Many2one('purchasing.team', string='Purchasing Team')

class ProductTemplate(models.Model):
    _inherit = "product.template"

    purchasing_team_id = fields.Many2one('purchasing.team', string='Purchasing Team', related='categ_id.purchasing_team_id', readonly=True, store=True)
