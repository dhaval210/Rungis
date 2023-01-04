# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TagetikAccount(models.Model):
     _name = 'account.account'
     _inherit = 'account.account'

     tagetik_account = fields.Char(string='Tagetik Account', required=True, help="Enter the corresponding Tagetik Account")

