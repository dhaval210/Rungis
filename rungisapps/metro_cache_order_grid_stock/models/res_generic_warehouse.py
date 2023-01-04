from odoo import api, fields, models


class GenericWarehouse(models.Model):
    _name = 'res.generic.warehouse'
    _description = 'generic warehouse mapping'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse')
    transit_in_ids = fields.Many2many(
        comodel_name='stock.picking.type',
        relation='wh_transit_in',
        domain="[('code', 'in', ['internal', 'incoming'])]"
    )
    transit_out_ids = fields.Many2many(
        comodel_name='stock.picking.type',
        relation='wh_transit_out',
        domain="[('code', 'in', ['internal', 'outgoing'])]"
    )
    receipt_in_id = fields.Many2one(
        comodel_name='stock.picking.type',
        domain="[('code', '=', 'incoming')]"
    )
