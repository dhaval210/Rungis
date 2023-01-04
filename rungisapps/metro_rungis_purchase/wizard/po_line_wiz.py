from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from openerp.exceptions import ValidationError


class POLineWizard(models.TransientModel):
    _name = 'po.line.wiz'
    _description = 'PO Line Wizard'

    po_id = fields.Many2one('purchase.order', string="Purchase Order")
    line_ids = fields.One2many('po.line.wiz.line', 'wiz_line_id', string="PO Lines")
    purpose = fields.Selection([('move_po_lines',"Move PO Lines"),('update_confirmed_qty', 'Update Confirmed Qty')], string="Purpose")
    
    @api.multi
    def force_rfq_send(self, po_ids):
        for order in po_ids:
            email_act = order.action_rfq_send()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=order.company_id.email)
                order.with_context(**email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
            order.is_supplier_notified = True
            order.button_confirm()
        return True

    def process(self):
        history_lines = []
        records_updated = []
        if self.purpose=='move_po_lines':
            for rec in self.line_ids:
                if rec.is_order_id_updated :
                    new_quantity=0
                    if not rec.order_id in records_updated:
                        records_updated.append(rec.order_id)
                    # code to get product desc of target PO as per vendor pricelist
                    desc_change = ''
                    target_vendor_id = rec.order_id.partner_id.id
                    is_product_available = False
                    if rec.product_id.seller_ids and rec.product_id.seller_ids.filtered(lambda p: p.name.id ==target_vendor_id):
                        seller_id = rec.product_id.seller_ids.filtered(lambda p: p.name.id ==rec.order_id.partner_id.id)
                        if seller_id[0].product_code and seller_id[0].product_name:
                            desc_change = '[' +seller_id[0].product_code + '] ' + seller_id[0].product_name
                        else:
                            desc_change = rec.product_id.display_name

                    if rec.order_id.order_line.filtered(lambda p: p.product_id.id ==rec.product_id.id):
                        # if same product_id exist in target PO then add the quantity and delete current PO line
                        line_id = rec.order_id.order_line.filtered(lambda p: p.product_id.id ==rec.product_id.id)
                        if len(line_id.ids) > 1:
                            line_id = self.env['product.product'].browse(max(line_id.ids))
                        
                        new_quantity = line_id.ordered_qty+rec.ordered_qty

                        product_cw_uom_qty = 0
                        product_cw_uom = False
                        if rec.product_id._is_cw_product():
                            product_cw_uom = rec.product_id.cw_uom_id.id
                            if rec.product_id.uom_id == line_id.product_id.uom_id:
                                product_cw_uom_qty = new_quantity * rec.product_id.average_cw_quantity
                            else:
                                product_uom_qty = rec.uom_id._compute_quantity(new_quantity, line_id.product_id.uom_id)
                                product_cw_uom_qty = product_uom_qty * rec.product_id.average_cw_quantity
                        line_id.write({'ordered_qty':new_quantity, 'product_qty':new_quantity,'product_cw_uom_qty' :product_cw_uom_qty, 'product_cw_uom':product_cw_uom})
                        line_id._onchange_ordered_qty()
                        rec.order_line_id.unlink() #delete present line from purchase.order.line
                        is_product_available = True                        
                    else:
                        rec.order_line_id.order_id = rec.order_id.id
                        new_quantity = rec.ordered_qty
                        rec.order_line_id.product_qty = new_quantity
                        rec.order_line_id._onchange_quantity()
                        rec.order_line_id._get_serial_number()
                        if desc_change:
                            rec.order_line_id.name = desc_change

                    # code for creating history records
                    if rec.order_id.state != 'draft' and rec.order_id.is_supplier_notified:
                        if rec.order_id.history_data.filtered(lambda p: p.product_id.id ==rec.product_id.id):
                            history_po_line = rec.order_id.history_data.filtered(lambda p: p.product_id.id ==rec.product_id.id)
                            history_vals = {'ordered_qty': new_quantity, 'product_qty' : new_quantity,'change_by': 'purchaser','is_sent':False}
                            history_po_line.write(history_vals)
                            rec.order_id.is_po_updated=True
                        else:
                            if is_product_available:
                                line_id = rec.order_id.order_line.filtered(lambda p: p.product_id.id ==rec.product_id.id)
                                prev_ordered_qty = new_quantity - rec.ordered_qty
                                prev_product_qty = line_id.prev_product_qty
                                history_id = [{
                                    'product_id': rec.product_id.id,
                                    'name': rec.product_desc,
                                    'product_uom': rec.uom_id.id,
                                    'product_qty': new_quantity,
                                    'ordered_qty': new_quantity,
                                    'prev_product_qty': prev_product_qty,
                                    'prev_ordered_qty': prev_ordered_qty,
                                    'order_id': rec.order_id.id,
                                    'orderline_id': rec.order_line_id.id,
                                    'change_by': 'purchaser',
                                    'is_sent': False,
                                    'is_new_line': False}]
                                rec.order_id.history_data = history_id
                                rec.order_id.is_po_updated = True
                            else:
                                history_id = [{
                                    'product_id': rec.product_id.id,
                                    'name': rec.product_desc,
                                    'product_uom': rec.uom_id.id,
                                    'product_qty': new_quantity,
                                    'ordered_qty': new_quantity,
                                    'prev_product_qty': new_quantity,
                                    'prev_ordered_qty': new_quantity,
                                    'order_id': rec.order_id.id,
                                    'orderline_id': rec.order_line_id.id,
                                    'change_by': 'purchaser',
                                    'is_sent': False,
                                    'is_new_line': True}]
                                rec.order_id.history_data = history_id
                                rec.order_id.is_po_updated = True

            if records_updated:
                # uncheck vendor confirmed quantity flag in PO 
                for po in records_updated:
                    po.is_vendor_qty_confirmed=False

                # update serial_number of current PO orderlines
                for line in self.po_id.order_line:
                    line._get_serial_number()
                self.force_rfq_send(records_updated)
        
        if self.purpose=='update_confirmed_qty':
            history_lines = []
            if self.po_id.state!='draft' and self.po_id.is_supplier_notified:
                update_history = True
            else:
                update_history = False
            for rec in self.line_ids:
                if rec.is_confirmed_qty_updated:
                    rec.order_line_id.product_qty = rec.confirmed_qty
                    if update_history:
                        if self.po_id.history_data.filtered(lambda p: p.orderline_id.id ==rec.order_line_id.id):
                            history_po_line =self.po_id.history_data.filtered(lambda p: p.orderline_id.id ==rec.order_line_id.id)
                            history_vals = {
                                'product_id': rec.product_id.id,
                                'name': rec.product_desc,
                                'product_uom': rec.uom_id.id,
                                'product_qty': rec.confirmed_qty,
                                'order_ids': self.po_id.id,
                                'orderline_id': rec.order_line_id.id,
                                'change_by': 'vendor',
                                'is_sent': True}
                            if history_po_line.is_sent==True:
                                history_vals['prev_product_qty'] = rec.prev_confirmed_qty
                            history_po_line.write(history_vals)
                            self.po_id.is_po_updated = True
                        else:
                            history_id = {
                                'product_id': rec.product_id.id,
                                'name': rec.product_desc,
                                'product_uom': rec.uom_id.id,
                                'product_qty': rec.confirmed_qty,
                                'ordered_qty': rec.ordered_qty,
                                'prev_product_qty': rec.prev_confirmed_qty,
                                'prev_ordered_qty': rec.ordered_qty,
                                'order_id': self.po_id.id,
                                'orderline_id': rec.order_line_id.id,
                                'change_by': 'vendor',
                                'is_sent': True}
                            history_lines.append(history_id)
                rec.order_line_id.is_vendor_qty_confirmed = True
            self.po_id.is_vendor_qty_confirmed = True
            if history_lines:
                self.po_id.history_data = history_lines
                self.po_id.is_po_updated = True
            return True


class POLineWizardLine(models.TransientModel):
    _name = 'po.line.wiz.line'
    _description = 'PO Line Wizard Lines'

    vendor_id = fields.Many2one('res.partner', string="Vendor")
    order_id = fields.Many2one('purchase.order', string="Purchase Order")
    order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")
    product_id = fields.Many2one('product.product', string="Product")
    product_desc = fields.Char(string="Desc")
    ordered_qty = fields.Float(string="Ordered Qty")
    confirmed_qty = fields.Float(string="Confirmed Qty")
    prev_confirmed_qty = fields.Float(string="Prev Confirmed Qty")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    wiz_line_id = fields.Many2one('po.line.wiz', string="Line")

    is_confirmed_qty_updated = fields.Boolean(string="Confirmed Qty Updated?" ,default=False)
    is_order_id_updated = fields.Boolean(string="Order Reference Updated?" ,default=False)

    @api.onchange('confirmed_qty')
    def _onchange_confirmed_qty(self):
        self.is_confirmed_qty_updated = True
        if self.confirmed_qty>self.ordered_qty:
            raise ValidationError(_('Confirmed Qty cannot be more than Ordered Qty.'))

    @api.onchange('order_id')
    def _onchange_order_id(self):
        self.is_order_id_updated = True
        self.vendor_id = self.order_id.partner_id.id