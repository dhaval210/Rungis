from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    date_expected = fields.Datetime(
        'Expected Date', index=True, required=False,
        states={'done': [('readonly', True)]},
        help="Scheduled date for the processing of this move", compute='_compute_date_expected', store=True)

    @api.depends('purchase_line_id.new_date_planned')
    def _compute_date_expected(self):
        for rec in self:
            rec.date_expected = (
                rec.purchase_line_id.new_date_planned or
                rec.purchase_line_id.date_planned or
                fields.Datetime.now()
            )
