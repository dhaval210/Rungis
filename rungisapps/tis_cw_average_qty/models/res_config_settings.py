# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_deviation_warning = fields.Boolean("Deviation Warning",
                                             implied_group='tis_cw_average_qty.group_deviation_warning')
