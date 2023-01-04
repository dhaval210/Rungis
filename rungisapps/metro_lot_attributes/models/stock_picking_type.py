from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    create_lot_attributes = fields.Boolean()
