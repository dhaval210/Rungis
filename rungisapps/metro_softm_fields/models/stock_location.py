from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    softm_location_number = fields.Integer('SoftM Lagernummer')
