from odoo import api, fields, models
import copy

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    s_loc_num = fields.Char(compute='_compute_location_number')

    @api.onchange('product_id')
    def _onchange_location_number(self):
        self.softm_location_number = self._default_location_number()

    def _default_location_number(self):
        for rec in self:
            if rec.orderpoint_id and rec.orderpoint_id.warehouse_id.softm_location_number > 0:
                return str(rec.orderpoint_id.warehouse_id.softm_location_number)
            if rec.order_id.picking_type_id.warehouse_id and rec.order_id.picking_type_id.warehouse_id.softm_location_number > 0:
                return str(rec.order_id.picking_type_id.warehouse_id.softm_location_number)
            if rec.product_id.softm_location_number:
                return str(rec.product_id.softm_location_number)
            return '0'

    softm_location_number = fields.Selection(
        string='Lagernummer',
        selection=[
            ('0', '0'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('20', '20'),
            ('50', '50'),
            ('51', '51'),
            ('54', '54'),
            ('57', '57'),
        ],
        default=_default_location_number,
        readonly=False
    )

    on_change_log = [
        'product_id',
        'product_qty',
        'price_unit',
        'softm_location_number',
        'date_planned'
    ]

    @api.model
    def create(self, values):
        line = super().create(values)
        if (
            line.order_id.name is not False and
            line.order_id.name[:3] == 'PO5' and
            line.order_id.state == 'purchase' and
            any(k in values for k in self.on_change_log)
        ):
            rec_id = copy.deepcopy(line.id)
            self.env['softm.order.line.log'].create({
                'order_lr_id': rec_id,
                'order_line_ref_id': rec_id,
                'mode': 'create'
            })
        if (
            not line.softm_location_number or
            line.softm_location_number == '0'
        ):
            line.softm_location_number = line._default_location_number()
        return line

    @api.multi
    def write(self, values):
        result = super().write(values)
        for rec in self:
            if (
                rec.order_id.name is not False and
                rec.order_id.name[:3] == 'PO5' and
                rec.order_id.state == 'purchase' and
                any(k in values for k in rec.on_change_log)
            ):
                rec_id = copy.deepcopy(rec.id)
                create_line = self.env['softm.order.line.log'].search([('order_lr_id', '=', rec_id), ('mode', '=', 'create')])
                if len(create_line) > 0:
                    self.env['softm.order.line.log'].create({
                        'order_lr_id': rec_id,
                        'order_line_ref_id': rec_id,
                        'mode': 'update'
                    })
        return result

    @api.multi
    def unlink(self):
        for rec in self:
            if (
                rec.order_id.name is not False and
                rec.order_id.name[:3] == 'PO5' and
                rec.order_id.state == 'purchase'
            ):
                rec_id = copy.deepcopy(rec.id)
                self.env['softm.order.line.log'].create({
                    'order_lr_id': rec_id,
                    'order_line_ref_id': rec_id,
                    'mode': 'delete'
                })
        result = super().unlink()
        return result
