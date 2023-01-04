from odoo import api, fields, models


class Batch(models.Model):
    _inherit = 'stock.picking.batch'

    tour_id = fields.Many2one(
        comodel_name='transporter.route',
        compute='_compute_route_id',
        store=True
    )

    hub_id = fields.Many2one(
        comodel_name='transporter.hub',
        compute='_compute_route_id',
        store=True
    )
    departure_time = fields.Datetime(compute='_compute_route_id', store=True)

    @api.depends('picking_ids.transporter_route_id')
    def _compute_route_id(self):
        for batch in self.filtered(lambda x: x.state not in ['done', 'cancel']):
            tour_id = False
            hub_id = False
            for pick in batch.picking_ids:
                tour_id = pick.transporter_route_id
                hub_id = tour_id.hub_id
                break
            batch.tour_id = tour_id
            batch.hub_id = hub_id
            if hub_id is not False:
                batch.departure_time = hub_id.departure_time


