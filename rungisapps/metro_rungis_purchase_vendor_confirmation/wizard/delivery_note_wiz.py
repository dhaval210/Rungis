from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from openerp.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class DeliveryNoteWizard(models.TransientModel):
    _name = 'delivery.note.wiz'
    _description = 'Delivery Note Wizard'
    
    po_id = fields.Many2one('purchase.order', string="Purchase Order")
    line_ids = fields.One2many('delivery.note.wiz.line', 'wiz_line_id', string="PO Lines")
        
    def process(self):
        records_updated = []
        for rec in self.line_ids:
            if rec.is_qty_updated:
                rec.order_line_id.prev_confirmed_qty = rec.product_qty
                rec.order_line_id.confirmed_qty = rec.confirmed_qty
                if rec.product_id.catch_weight_ok:
                    rec.order_line_id.product_cw_uom_qty_confirmed = rec.confirmed_qty_cw
                picking_ids = self.env['stock.picking'].search([('origin', '=', self.po_id.name)])
                if picking_ids:
                    for picking_id in picking_ids:
                        if picking_id.state not in ['done','cancel']:
                            for move in picking_id.move_ids_without_package.filtered(lambda x: x.product_id.id == rec.product_id.id):
                                if rec.confirmed_qty != 0: 
                                    move.product_uom_qty = rec.confirmed_qty
                                    if rec.product_id.catch_weight_ok:
                                        move.product_cw_uom_qty = rec.confirmed_qty_cw
                                else:
                                    move.unlink_moves_with_ref_po()
                            for lines in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id.id == rec.product_id.id):
                                lines.product_uom_qty = rec.confirmed_qty
                                if rec.product_id.catch_weight_ok:
                                    lines.product_cw_uom_qty = rec.confirmed_qty_cw
                
            rec.order_line_id.price_unit_dn = rec.price_unit_dn 
            if rec.calculated_lpp_price:
                rec.product_id.last_purchase_price = rec.calculated_lpp_price
            rec.is_vendor_qty_confirmed=True
        self.po_id.is_delivery_note_check = True

        # code to add channel in the follower list of existing purchase order
        channel_ids = self.env['ir.config_parameter'].sudo().get_param('po_follower_channel_visible')
        if channel_ids:
            channel_ids = [int(x) for x in channel_ids.replace(' ', '').split(',')]
            channel_id_obj = self.env['mail.channel'].sudo().search([('id','in', channel_ids)])
            ch_id_lst = []
            for ch_id in channel_id_obj:
                ch_id_lst.append((4,ch_id.id))
            if ch_id_lst:
                try:
                    mail_invite = self.env['mail.wizard.invite'].with_context({
                        'default_res_model':'purchase.order',
                        'default_res_id':self.po_id.id
                        }).sudo().create({
                            'channel_ids': ch_id_lst,
                            'send_mail':False
                        })
                    mail_invite.add_followers()
                except:
                    pass

class DeliveryNoteWizardLine(models.TransientModel):
    _name = 'delivery.note.wiz.line'
    _description = 'Delivery Note Wizard Lines'
    
    order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")
    product_id = fields.Many2one('product.product', string="Product", related="order_line_id.product_id")
    product_desc = fields.Text(string="Description", related="order_line_id.name")
    price_unit = fields.Float(string="Unit Price", related="order_line_id.price_unit")
    product_qty = fields.Float(string="Ordered Qty",  related="order_line_id.product_qty")
    uom_id = fields.Many2one('uom.uom', string="UOM", related="order_line_id.product_uom")
    confirmed_qty = fields.Float(string='Confirmed Quantity', digits=dp.get_precision('Product Unit of Measure'))
    confirmed_qty_cw = fields.Float(string='Confirmed CW-Qty', default=0.0, digits=dp.get_precision('Product CW Unit of Measure'))
    confirmed_cw_uom_id = fields.Many2one('uom.uom', string="CW-UOM", related="order_line_id.product_cw_uom")
    price_unit_dn = fields.Float(string='Unit Price(DN)', digits=dp.get_precision('Unit Price(DN)'))
    calculated_lpp_price = fields.Float(string='LPP', digits=dp.get_precision('Unit Price(DN)'))

    is_qty_updated = fields.Boolean(string="Line Updated?" ,default=False)
    is_price_updated = fields.Boolean(string="Line Updated?" ,default=False)

    
    wiz_line_id = fields.Many2one('delivery.note.wiz', string="Line")

    @api.onchange('price_unit_dn')
    def _onchange_price_unit_dn(self):
        self.is_price_updated = True
        if self.product_id.categ_id and self.product_id.categ_id.is_unit_price_dn_maintainable:
                computed_lpp = self.product_id.uom_id._compute_lpp_quantity(self.price_unit_dn, self.uom_id)



    @api.onchange('confirmed_qty')
    def _onchange_confirmed_qty(self):
        if self.confirmed_qty>self.product_qty:
            raise ValidationError(_('Confirmed Qty cannot be more than Ordered Qty.'))
        product_cw_uom_qty = 0
        self.is_qty_updated = True
        if self.product_id._is_cw_product():
            if self.uom_id == self.product_id.uom_id:
                self.confirmed_qty_cw = self.confirmed_qty * self.product_id.average_cw_quantity
            else:
                product_uom_qty = self.uom_id._compute_quantity(self.confirmed_qty, self.product_id.uom_id)
                self.confirmed_qty_cw = product_uom_qty * self.product_id.average_cw_quantity

    @api.onchange('confirmed_qty_cw')
    def _onchange_confirmed_qty_cw(self):
        if not self.product_id._is_cw_product():
            raise ValidationError(_('You cannot add CW-QTY for Non-Catch Weight Product.'))
        else:
            self.is_qty_updated = True

