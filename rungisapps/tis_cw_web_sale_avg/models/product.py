# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_cw_qty(self):
        return self.average_cw_quantity
