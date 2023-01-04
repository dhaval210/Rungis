# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """inherit inventory config and add two booleans"""
    _inherit = 'res.config.settings'

    same_page = fields.Boolean(string='Print Report In Same Page:',
                               default=False)

    separate_pages = fields.Boolean(string='Print Report In Separate '
                                           'Pages:', default=False)

    print_on = fields.Selection(
        selection=[
            ('validate', 'Validation'),
            ('line', 'Line writing'),
        ],
        default='validate'
    )

    @api.onchange('same_page')
    def change_same_page(self):
        """onchange"""
        if self.same_page:
            self.separate_pages = False

    @api.onchange('separate_pages')
    def change_separate_pages(self):
        """onchange"""
        if self.separate_pages:
            self.same_page = False

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            same_page=get_param('metro_barcode_print_community.same_page'),
            separate_pages=get_param('metro_barcode_print_community.separate_pages'),
            print_on=get_param('metro_barcode_print_community.print_on')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("metro_barcode_print_community.same_page",
                          self.same_page)
        ICPSudo.set_param("metro_barcode_print_community.separate_pages",
                          self.separate_pages)
        ICPSudo.set_param("metro_barcode_print_community.print_on",
                          self.print_on)
