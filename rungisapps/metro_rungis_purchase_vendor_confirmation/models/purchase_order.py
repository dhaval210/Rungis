from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_unit_price_dn_maintainable = fields.Boolean(string='Unit Price DN Maintainable?', copy=False)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_delivery_note_check = fields.Boolean(string='Delivery Note Checked?', copy=False)
    is_group_delivey_note = fields.Boolean(compute='_compute_delivery_note_group', string='Is Delivery Note Group?', copy=False)
   
    @api.depends('is_group_delivey_note')
    def _compute_delivery_note_group(self):
        for rec in self:
            if self.env.user.has_group('metro_rungis_purchase_vendor_confirmation.group_delivery_note'):
                rec.is_group_delivey_note=True
            else:
                rec.is_group_delivey_note=False

    @api.multi
    def action_delivery_note_wiz(self):
        view = self.env.ref('metro_rungis_purchase_vendor_confirmation.form_delivery_note_wiz')
        line_ids_vals = []
        for rec in self.order_line:
            vals = {
                'order_line_id' : rec.id,
                'confirmed_qty' : rec.confirmed_qty,
                'confirmed_qty_cw' : rec.product_cw_uom_qty_confirmed,
                'price_unit_dn' : rec.price_unit_dn,
            }
            if not rec.confirmed_qty:
                vals['confirmed_qty'] = rec.product_qty
            if not rec.product_cw_uom_qty_confirmed:
                vals['confirmed_qty_cw'] = rec.product_cw_uom_qty
            if not rec.price_unit_dn:
                vals['price_unit_dn'] = rec.price_unit

            line_ids_vals.append([0,0,vals])
        wiz = self.env['delivery.note.wiz'].create({'po_id': self.id, 'line_ids' : line_ids_vals})
        ctx = dict(self._context)
        return {
                'name': _('Delivery Note '),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delivery.note.wiz',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': ctx,
            }
    @api.multi
    def action_delivery_note_wiz_undo(self):
        self.is_delivery_note_check = False

        # remove channel_ids from following list
        channel_ids = self.env['ir.config_parameter'].sudo().get_param('po_follower_channel_visible')
        if channel_ids:
            # channel_ids = channel_ids.replace(' ', '')
            channel_ids = [int(x) for x in channel_ids.replace(' ', '').split(',')]
            self.sudo().message_unsubscribe(channel_ids=channel_ids)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_unit_dn = fields.Float(string='Unit Price(DN)', digits=dp.get_precision('Unit Price(DN)'), copy=False)
    confirmed_qty = fields.Float(string='Confirmed Quantity', digits=dp.get_precision('Product Unit of Measure'), store=True, copy=False)
    prev_confirmed_qty = fields.Float(string='Prev Confirmed Quantity', digits=dp.get_precision('Product Unit of Measure'), store=True,  copy=False)
    product_cw_uom_qty_confirmed = fields.Float(string='Confirmed CW-Qty', default=0.0, digits=dp.get_precision('Product CW Unit of Measure'),  copy=False)
    is_vendor_qty_confirmed = fields.Boolean(string='Vendor QTY Confirmed', default=False, copy=False)

 
    @api.model
    def create(self, vals):
        # if PO is created from other source then this code will fullfills confirmed_qty automatically
        if not vals.get('confirmed_qty'):
            vals['confirmed_qty'] = vals.get('product_qty') or 0
        if not vals.get('price_unit_dn'):
            vals['price_unit_dn'] = vals.get('price_unit') or 0
        res = super(PurchaseOrderLine, self).create(vals)
        if res.product_id.catch_weight_ok:
            res.product_cw_uom_qty_confirmed=res.product_cw_uom_qty
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.confirmed_qty = self.product_qty
        self.is_vendor_qty_confirmed = False
        return res