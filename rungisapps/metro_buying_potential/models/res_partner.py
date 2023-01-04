# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    buying_potential = fields.Float('Yearly Buying potential', oldname='target')
    sales_target = fields.Float('Yearly Sales Target')
    total_invoiced = fields.Monetary(store=True)

    @api.depends('invoice_ids.state')
    def _invoice_total(self):
        return super(ResPartner, self)._invoice_total()
