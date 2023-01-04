from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    allow_batch_assignment = fields.Boolean()
