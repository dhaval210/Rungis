# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_catch_weight = fields.Boolean("Catch Weight", implied_group='tis_catch_weight.group_catch_weight')
    module_tis_cw_average_qty = fields.Boolean("Average Quantity on CW Products")
    module_tis_cw_theme = fields.Boolean("Catch Weight Theme")
    module_tis_cw_procurement = fields.Boolean("Catch Weight Procurement")
    module_tis_cw_mrp = fields.Boolean("Catch Weight in Manufacturing")
    module_tis_cw_sale_mrp = fields.Boolean("Catch Weight Sale and MRP Management")
    module_tis_cw_purchase_mrp = fields.Boolean("Catch weight Purchase and MRP Management")
    module_tis_cw_mrp_byproduct = fields.Boolean("Catch Weight in Manufacturing By-Products")
    module_tis_cw_demo_data = fields.Boolean(" CW Products Demo Data")
    module_tis_cw_stock_report_xls = fields.Boolean("Catch Weight Stock Report")
    module_tis_cw_web_sale_avg = fields.Boolean("Average Quantity in Ecommerce")
    module_tis_cw_web_sale = fields.Boolean("Catch Weight in E-commerce")
    module_all_channels_sales_cw_report = fields.Boolean("Catch Weight in Channels Sales Report")
    module_tis_cw_stock_picking_batch = fields.Boolean("Catch Weight in Batch Picking")
