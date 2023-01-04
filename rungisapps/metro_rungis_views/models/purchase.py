from odoo import models, api, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_ref = fields.Char('Vendor Int. Ref.', related='partner_id.ref')
    check_done_channel_ids = fields.Many2many('mail.channel', 'check_done_channel_rel',
                                              compute='_compute_check_done_channel_ids')

    @api.depends('message_channel_ids')
    def _compute_check_done_channel_ids(self):
        channel_ids = self.env['ir.config_parameter'].sudo().get_param('po_follower_channel_visible')
        if channel_ids:
            channel_ids = channel_ids.replace(' ', '').split(',')
        for rec in self:
            rec.check_done_channel_ids = rec.message_channel_ids.sudo().\
                filtered(lambda res: str(res.id) in channel_ids)

    def button_softm_refresh(self):
        date = self.po_date_planned
        self.po_date_planned = fields.Datetime.now()
        self.po_date_planned = date


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        """
        Function supering for adding the product code
        in the description.
        """
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.product_id:
            return res

        product_lang = self.product_id.with_context(
            lang=self.partner_id.lang,
            partner_id=self.partner_id.id,
        )
        partner_id = self.partner_id
        seller_id = product_lang.seller_ids.filtered(lambda r: r.name == partner_id and (not r.product_id or r.product_id == self.product_id))\
            .sorted(key=lambda r: r.min_qty)
        if seller_id:
            product_code = seller_id[0].product_code if seller_id else False
            product_name = seller_id[0].product_name if seller_id else False
            if product_code:
                if not product_name:
                    product_name = product_lang.name
                self.name = "[" + product_code + "] " + product_name
                if product_lang.description_purchase:
                    self.name += '\n' + product_lang.description_purchase
            elif product_name and product_lang.default_code:
                self.name = "[" + product_lang.default_code + "] " + product_name
                if product_lang.description_purchase:
                    self.name += '\n' + product_lang.description_purchase

        return res
