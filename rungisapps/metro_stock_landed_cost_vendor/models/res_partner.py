# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    landed_cost_journal_id = fields.Many2one('account.journal', string="Landed Cost Journal")
    landed_cost_line_ids = fields.One2many('vendor.landed.cost.line',
                                           'partner_id', string="Landed Costs")

    later_income_journal_id = fields.Many2one('account.journal', string="Later Income Journal")
    later_income_line_ids = fields.One2many('later.income.line', 'partner_id', string="Later Income")
    landed_cost_aggregate = fields.Float(string="SUM LC(%)", compute="_compute_landed_cost_sum")
    later_income_aggregate = fields.Float(string="SUM LI(%)", compute="_compute_later_income_sum")

    @api.multi
    @api.depends('landed_cost_line_ids.percentage')
    def _compute_landed_cost_sum(self):
        for rec in self:
            total = 0
            for line in rec.landed_cost_line_ids:
                total += line.percentage
            rec.landed_cost_aggregate = total

    @api.multi
    @api.depends('later_income_line_ids.percentage')
    def _compute_later_income_sum(self):
        for rec in self:
            total = 0
            for line in rec.later_income_line_ids:
                total += line.percentage
            rec.later_income_aggregate = total


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    landed_cost_aggregate = fields.Float(string="SUM LC(%)",
                                         related='name.landed_cost_aggregate')
    later_income_aggregate = fields.Float(string="SUM LI(%)",
                                         related='name.later_income_aggregate')
