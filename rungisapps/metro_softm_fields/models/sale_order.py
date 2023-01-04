from odoo import api, fields, models


class MetroExtend_SaleOrder(models.Model):
    _inherit = 'sale.order'

    send_to_softm = fields.Boolean(string="SoftM Status")
    tour_id = fields.Many2one(comodel_name='transporter.route')
    run_up_point = fields.Integer(string="Anlaufpunkt")
    softm_trennen = fields.Boolean(string="Trennen", compute="_compute_softm_trennen")

    @api.depends('order_line')
    def _compute_softm_trennen(self):
        for rec in self.filtered(lambda x: x.state in ['draft', 'sent']):
            if any(ol.delivery_no is not False and len(ol.delivery_no) > 0 for ol in rec.order_line):
                rec.softm_trennen = True
            else:
                rec.softm_trennen = False

    @api.multi
    def action_confirm(self):
        res = super(MetroExtend_SaleOrder, self).action_confirm()
        for record in self:
            record.picking_ids.write({'run_up_point': record.run_up_point})
        return res    


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    special_wishes = fields.Char(string="Sonderwünsche")
    so_pos_no = fields.Char(string ="SO POS NO")
    process_number = fields.Integer(string="Vorgangsnummer (Mehrplatzlager)")
    process_position = fields.Integer(
        string="Vorgangsposition (Mehrplatzlager)"
    )
    delivery_no = fields.Char(string="Lieferschein Nr.")


    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super()._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({
            'special_wishes': self.special_wishes,
            'process_number': self.process_number,
            'process_position': self.process_position,
            'tour_id': self.order_id.tour_id.id,
        })
        return values
