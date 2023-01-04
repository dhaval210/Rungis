from odoo import api, fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    async_pick = fields.Boolean(default=False)


class PickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    async_pick = fields.Boolean(default=False)
