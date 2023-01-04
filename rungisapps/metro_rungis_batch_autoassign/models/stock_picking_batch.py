from odoo import api, fields, models


class PickingBatch(models.Model):
    _inherit = 'stock.picking.batch'
    _order = 'departure_time'

    type_id = fields.Integer()
    group_id = fields.Integer()

    oldest_date = fields.Datetime(compute='_compute_oldest_date', store=True)

    @api.depends('picking_ids', 'state')
    def _compute_oldest_date(self):
        for rec in self.filtered(lambda x: x.state == 'in_progress'):
            sale_ids = rec.picking_ids.mapped('sale_id')
            if len(sale_ids):
                sale_id = sale_ids.sorted(key=lambda l: l.create_date)[0]
                if sale_id:
                    rec.oldest_date = sale_id.create_date
