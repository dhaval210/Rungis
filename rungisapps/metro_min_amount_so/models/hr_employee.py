# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class Employee(models.Model):
    _inherit = "hr.employee"

    company_currency_id = fields.Many2one('res.currency', related='address_id.company_id.currency_id', string="Company Currency",
                                          readonly=True, help='Utility field to express amount currency', store=True)
    min_amount_employee = fields.Monetary(string="Minimum amount to confirm SO for Employee",
                                          help="This will trigger a blocking warning at SO-Confirmation if this value exceeds the total SO amount. Set to 0 for no limit.",
                                          currency_field='company_currency_id')
