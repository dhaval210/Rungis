from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    softm_location_number = fields.Integer('SoftM Lagernummer')
