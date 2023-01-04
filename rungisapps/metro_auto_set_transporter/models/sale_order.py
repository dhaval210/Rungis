from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for record in self:
            if record.partner_id.transporter_id:
                record.picking_ids.write({'transporter_route_id': record.partner_id.tour_id.id})
            else:
                record.picking_ids.write({'transporter_route_id': record.tour_id.id})
        return res
