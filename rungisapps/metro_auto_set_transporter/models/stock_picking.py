from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for record in self:
            # Get Supplier
            supplier = self.env['res.partner'].browse(record.partner_id.id)
            # If transporter_id is set on res.partner, add to stock.picking
            if supplier.transporter_id:
                record.transporter_id = supplier.transporter_id.id
        return
