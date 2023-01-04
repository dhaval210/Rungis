from odoo import api, fields, models, _


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'
    _description = 'Batch Picking'

    @api.multi
    def done(self):
        for batch in self:
            pickings = batch.picking_ids
            for picking in pickings:
                if picking.gate_id:
                    picking.gate_id.state = False
        return super(StockPickingBatch, self).done()
