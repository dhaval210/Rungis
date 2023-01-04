# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Company(models.Model):
    _inherit = "res.company"

    min_amount_customer = fields.Monetary(string="Minimum amount to confirm SO for non KAC",
                                        help="This will trigger a blocking warning at SO-Confirmation if this value exceeds the total SO amount. Set to 0 for no limit.",
                                        currency_field='currency_id')
    min_amount_kac_customer = fields.Monetary(string="Minimum amount to confirm SO for KAC",
                                        help="This will trigger a blocking warning at SO-Confirmation if this value exceeds the total SO amount. Set to 0 for no limit.",
                                        currency_field='currency_id')
    employee_delivery_address_ids = fields.Many2many('res.partner', string='Employee Delivery Addresses',
                                                     help='Sets the domain on the Delivery Address field on the SO if the Partner is an Employee')
