# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    landed_cost_journal_id = fields.Many2one('account.journal', string="Landed Cost Journal")
    later_income_journal_id = fields.Many2one('account.journal', string="Later Income Journal")



