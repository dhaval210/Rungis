from odoo import api, fields, models
from odoo.exceptions import UserError


class PickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    location_id = fields.Many2one(
        comodel_name='stock.location',
        compute='_compute_location_id',
        store=True
    )

    @api.depends('picking_ids')
    def _compute_location_id(self):
        for batch in self.filtered(lambda x: x.state not in ['done', 'cancel']):
            location_id = 0
            first = True
            for pick in batch.picking_ids:
                if first is True:
                    location_id = pick.location_id
                    first = False
                    continue
                if location_id != pick.location_id:
                    pass
                    # raise UserError('there is a mismatch between source locations')
            batch.location_id = location_id
