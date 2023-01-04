from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
from odoo.addons.purchase.models.purchase import PurchaseOrderLine as POLine
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_mail_sent_fail = fields.Boolean(string="Mail Sent Failed", compute="compute_is_mail_sent_fail")

    def compute_is_mail_sent_fail(self):
        channel_ids = self.env['ir.config_parameter'].sudo().get_param('po_follower_channel_visible')
        if channel_ids:
            channel_ids = channel_ids.replace(' ', '').split(',')
        for rec in self:
            check_done_channel_ids = rec.check_done_channel_ids.sudo().filtered(lambda res: str(res.id) in channel_ids)
            rec.is_mail_sent_fail = False
            mail_ids = self.env['mail.mail'].sudo().search([('model', '=', 'purchase.order'), ('res_id', '=', rec.id)])
            if any(mail.state == 'exception' for mail in mail_ids) or not rec.is_supplier_notified or any(x.is_sent == False for x in rec.history_data):
                if not check_done_channel_ids:
                    rec.is_mail_sent_fail = True


def _onchange_quantity_patch(self):
    if not self.product_id:
        return
    params = {'order_id': self.order_id}
    seller = self.product_id._select_seller(
        partner_id=self.partner_id,
        quantity=self.product_qty,
        date=self.order_id.date_order and self.order_id.date_order.date(),
        uom_id=self.product_uom,
        params=params)

    if seller or not self.date_planned:
        self.date_planned = self._get_date_planned(seller).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)

    if seller or not self.date_planned:
        self.date_planned = self._get_date_planned(seller).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)

    if not seller:
        return


POLine._onchange_quantity = _onchange_quantity_patch


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('price_unit')
    def _check_unit_price(self):
        for rec in self:
            if rec.product_id and rec.price_unit <= 0:
                raise ValidationError(
                    _('Buying price 0 is not allowed, please enter a buying price bigger then 0.'))

    def merge_moves_of_po(self, move, move_to_merge):
        move._do_unreserve()
        move_to_merge._do_unreserve()
        move_to_merge.write({
            'state': 'draft'
        })
        move.product_uom_qty += move_to_merge.product_uom_qty
        move.product_cw_uom_qty += move_to_merge.product_cw_uom_qty
        move_to_merge.unlink()
        move._action_assign()

    @api.multi
    def write(self, values):
        res = super(PurchaseOrderLine, self).write(values)
        if 'product_qty' in values and self.state == 'purchase':
            po = self.order_name
            pickings = self.env['stock.picking'].search([('origin', '=', po), ('company_id', '=', self.company_id.id)])
            for rec in pickings:
                if rec.state != 'done':
                    moves = rec.move_ids_without_package.filtered(lambda x: x.product_id.id == self.product_id.id)
                    if len(moves) > 1:
                        self.merge_moves_of_po(moves[0], moves[-1])
                    else:
                        for move in moves:
                            if values['product_qty'] != 0:
                                if 'product_qty' in values:
                                    move.product_uom_qty = values['product_qty']
                                if self.product_id.catch_weight_ok:
                                    if 'product_cw_uom_qty' in values:
                                        move.product_cw_uom_qty = values['product_cw_uom_qty']
                            else:
                                move.unlink_moves_with_ref_po()
                        for lines in rec.move_line_ids_without_package.filtered(
                                lambda x: x.product_id.id == self.product_id.id):
                            if 'product_qty' in values:
                                lines.product_uom_qty = values['product_qty']
                            if self.product_id.catch_weight_ok:
                                if 'product_cw_uom_qty' in values:
                                    lines.product_cw_uom_qty = values['product_cw_uom_qty']
        return res

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)
        if not seller and self.product_qty == 0:
            return

        return super(PurchaseOrderLine, self)._onchange_quantity()

    def _suggest_quantity(self):
        super(PurchaseOrderLine, self)._suggest_quantity()
        seller_min_qty = self.product_id.seller_ids \
            .filtered(lambda r: r.name == self.order_id.partner_id and (
                    not r.product_id or r.product_id == self.product_id)) \
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.price_unit = seller_min_qty[0].price