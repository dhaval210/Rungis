# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    average_cw_quantity = fields.Float(string='Average CW Quantity',
                                       digits=dp.get_precision('Product CW Unit of Measure'))
