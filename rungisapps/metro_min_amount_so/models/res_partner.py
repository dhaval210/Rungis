# -*- coding: utf-8 -*-

from odoo import api, fields, models

class KeyAccountCustomer(models.Model):
    _inherit = "res.partner"

    kac = fields.Boolean(string="Key Account Customer", default=False, help="This field identifies if the contact is a Key Account Customer")

    @api.model
    def _commercial_fields(self):
        res = super(KeyAccountCustomer, self)._commercial_fields()
        res.append('kac')
        return res
