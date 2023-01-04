from odoo import api, fields, models
import copy


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    on_change_log = [
        'name',
        'partner_id',
        'currency_id',
        'company_id',
        'date_order'
    ]

    def button_confirm(self):
        if self.name is not False and self.name[:3] == 'PO5':
            self.env['softm.order.log'].create({
                'order_r_id': self.id,
                'order_ref_id': self.id,
                'mode': 'create'
            })
            for line in self.order_line:
                rec_id = copy.deepcopy(line.id)
                self.env['softm.order.line.log'].create({
                    'order_lr_id': rec_id,
                    'order_line_ref_id': rec_id,
                    'mode': 'create'
                })
        res = super().button_confirm()
        return res

    def write(self, vals):
        result = super().write(vals)
        if (
            self.name is not False and
            self.name[:3] == 'PO5' and
            self.state == 'purchase' and
            any(k in vals for k in self.on_change_log)
        ):
            self.env['softm.order.log'].create({
                'order_r_id': self.id,
                'order_ref_id': self.id,
                'mode': 'update'
            })
        return result

    @api.multi
    def unlink(self):
        for rec in self:
            if (
                self.name is not False and
                rec.name[:3] == 'PO5' and
                rec.state == 'purchase'
            ):
                self.env['softm.order.log'].create({
                    'order_r_id': rec.id,
                    'order_ref_id': rec.id,
                    'mode': 'delete'
                })
        result = super().unlink()
        return result
