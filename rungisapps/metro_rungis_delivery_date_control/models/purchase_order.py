from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    po_date_planned = fields.Datetime(string='Scheduled Date', track_visibility='onchange', default=False)
    status_check = fields.Boolean("Receipt status check", default=False, compute='compute_receipt_status')

    @api.model
    def create(self, values):
        if 'date_planned' in values and 'po_date_planned' not in values:
            values.update({
                'po_date_planned': values['date_planned']
            })
        if 'po_date_planned' not in values and 'order_line' in values:
            for line in values['order_line']:
                if isinstance(line[2], dict) and 'date_planned' in line[2]:
                    values.update({
                        'po_date_planned': line[2]['date_planned']
                    })
                    break

        return super().create(values)

    @api.multi
    def write(self, values):
        new_date = False
        if 'po_date_planned' in values:
            new_date = values['po_date_planned']
        res = super().write(values)
        if new_date is not False:
            for rec in self:
                rec.order_line.write({
                    'date_planned': new_date
                })
        return res

    def compute_receipt_status(self):
        for rec in self.picking_ids:
            if rec.state == 'done':
                self.status_check = not self.status_check
            else:
                return self.status_check

    @api.multi
    def action_set_date_planned(self):
        res = super(PurchaseOrder, self).action_set_date_planned()
        for order in self:
            order.order_line.update({'new_date_planned': order.po_date_planned})
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self.order_line:
            if not order.new_date_planned:
                order.new_date_planned = self.po_date_planned
            order.date_planned = self.po_date_planned
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    new_date_planned = fields.Datetime(
        string='Scheduled Date',
        compute='_compute_date_planned_line',
        store=True
    )

    @api.model
    def create(self, vals):
        if 'order_id' in vals:
            po = self.env['purchase.order'].browse([vals['order_id']])
            if po.id is not False and po.po_date_planned is not False:
                vals.update({
                    'date_planned': po.po_date_planned
                })

        return super().create(vals)

    @api.multi
    def write(self, values):
        for rec in self:
            if (
                (
                    'date_planned' not in values and
                    rec.order_id.po_date_planned != rec.date_planned and
                    rec.order_id.po_date_planned is not False
                ) or
                (
                    'date_planned' in values and
                    values['date_planned'] != rec.order_id.po_date_planned
                )
            ):
                values.update({
                    'date_planned': rec.order_id.po_date_planned,
                })
                break
        return super().write(values)

    @api.depends('order_id.po_date_planned')
    def _compute_date_planned_line(self):
        for rec in self:
            if rec.new_date_planned is False:
                rec.new_date_planned = rec.order_id.po_date_planned
