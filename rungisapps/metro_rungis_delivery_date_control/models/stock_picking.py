from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "stock.picking"

    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, track_visibility='onchange',
        help="Scheduled time for the first part of the shipment to be processed. "
             "Setting manually a value here would set it as expected date for all the stock moves.")

    @api.depends('move_lines.date_expected')
    def _compute_scheduled_date(self):
        for rec in self:
            if rec.move_type == 'direct':
                rec.scheduled_date = min(rec.move_lines.mapped('date_expected') or [fields.Datetime.now()])
            else:
                rec.scheduled_date = max(rec.move_lines.mapped('date_expected') or [fields.Datetime.now()])

    @api.one
    def _set_scheduled_date(self):
        self.move_lines.write({'date_expected': self.scheduled_date})
