from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    split_by_capacity = fields.Boolean('Split By capacity')
