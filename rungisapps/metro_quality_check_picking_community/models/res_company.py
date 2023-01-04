# # -*- coding: utf-8 -*-
# 
# from odoo import fields, models
# 
# class ResCompany(models.Model):
#     _inherit = "res.company"
#     
#     vehicle_product_id = fields.Many2one(
#         'product.product',
#         string='Vehicle Condition Product',
#     )
#     starcking_product_id = fields.Many2one(
#         'product.product',
#         string='Stacking Product',
#     )
#     door_product_id = fields.Many2one(
#         'product.product',
#         string='Vehicle Door Product',
#     )
#     temprature_product_id = fields.Many2one(
#         'product.product',
#         string='Temperature Product',
#     )
#     custom_quality_team_id = fields.Many2one(
#         'quality.alert.team',
#         string='Quality Team',
#     )