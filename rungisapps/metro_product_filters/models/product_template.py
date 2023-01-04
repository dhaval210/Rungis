# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_recording_rule = fields.Boolean("Has Recording Rule",
                                       compute='_check_reordering_rule',
                                       search='search_recording_rule')
    no_recording_rule = fields.Boolean("No Recording Rule",
                                       compute='_check_reordering_rule',
                                       search='search_no_recording_rule')

    def _check_reordering_rule(self):
        for res in self:
            if res.nbr_reordering_rules == 1:
                res.is_recording_rule = True
                res.no_recording_rule = False
            else:
                res.is_recording_rule = False
                res.no_recording_rule = True

    @api.multi
    def search_recording_rule(self, operator, value):

        return [('id', 'in', [x.id for x in self.search([]) if
                              x.is_recording_rule])]

    def search_no_recording_rule(self, operator, value):

        return [('id', 'in', [x.id for x in self.search([]) if
                              x.no_recording_rule])]