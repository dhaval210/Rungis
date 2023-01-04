# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    prev_product_qty = fields.Float(string='Previous Quantity', digits=dp.get_precision('Product Unit of Measure'),
                                    store=True)

    @api.multi
    def write(self, values):
        for rec in self:
            if rec and rec.order_id:
                if 'product_qty' in values and rec.product_qty != values.get('product_qty'):
                    values['prev_product_qty'] = rec.product_qty
        return super(PurchaseOrderLine, self).write(values)

    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        if res and res.order_id.state != 'draft' and res.order_id.is_supplier_notified:
            history_id = {
                'product_id': vals.get('product_id'),
                'name': vals.get('name'),
                'product_uom': vals.get('product_uom'),
                'prev_product_qty':  vals.get('product_qty'),
                'product_qty': vals.get('product_qty'),
                'order_id': res.order_id.id,
                'orderline_id': res.id,
                'is_sent': False,
                'is_new_line': True
            }
            res.order_id.history_data = [history_id]
            res.order_id.is_po_updated = True
        return res

    @api.multi
    def unlink(self):
        # unlink all the history records for the same line except the deleted history records
        for rec in self:
            po_history_ids = self.env['purchase.order.history'].search([('orderline_id', '=', rec.id), ('is_unlink_line', '=', False)])
            if po_history_ids:
                po_history_ids.unlink()
        return super(PurchaseOrderLine, self).unlink()


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_po_updated = fields.Boolean(string="IS PO Updated?", default=False, copy=False)
    history_data = fields.One2many('purchase.order.history', 'order_ids', string='History', copy=False)
    is_supplier_notified = fields.Boolean(string='Supplier Notified', default=False, copy=False)

    def get_history_lines_new(self):
        new_lines = self.history_data.filtered(
            lambda x:   x.is_sent==False and x.is_new_line==True and x.product_qty!=0)
        return new_lines

    def get_history_deleted_lines(self):
        deleted_lines = self.history_data.filtered(
            lambda x:   x.is_sent==False and x.is_unlink_line==True)
        return deleted_lines

    def get_history_lines_old(self):
        edited_lines = self.history_data.filtered(
            lambda x:  x.is_sent==False and x.is_unlink_line==False and  x.is_new_line==False )
        return edited_lines


    def get_lines_without_zero_qty(self):
        lines_with_zero_qty = self.order_line.filtered(lambda x: x.product_qty != 0)
        return lines_with_zero_qty

    @api.multi
    def write(self, values):
        if self.state != 'draft' and values.get('order_line') and self.is_supplier_notified:
            order_line = values['order_line']
            history_lines = []
            for line in order_line:
                
                if line[0] == 1:  # edit line
                    po_line_id = self.env['purchase.order.line'].browse(line[1])
                    line_vals = line[2]

                    if self.history_data.filtered(lambda p: p.orderline_id.id == po_line_id.id):
                        history_po_line = self.history_data.filtered(lambda p: p.orderline_id.id == po_line_id.id)
                        if 'product_qty' in line_vals:
                            history_vals = {
                                'product_id':line_vals.get('product_id') or po_line_id.product_id.id,
                                'name': line_vals.get('name') or po_line_id.product_id.name,
                                'product_uom': line_vals.get('product_uom') or po_line_id.product_uom.id,
                                'product_qty': line_vals.get('product_qty'),
                                'order_id': self.id,
                                'is_sent': False
                            }

                            if history_po_line.is_sent==True:
                                history_vals['prev_product_qty'] = po_line_id.product_qty
                            history_po_line.write(history_vals)
                            self.is_po_updated = True

                    else:
                        if 'product_qty' in line_vals:
                            history_id = {
                                'product_id':line_vals.get('product_id') or po_line_id.product_id.id,
                                'name': line_vals.get('name') or po_line_id.product_id.name,
                                'product_uom': line_vals.get('product_uom') or po_line_id.product_uom.id,
                                'prev_product_qty': po_line_id.product_qty,
                                'product_qty': line_vals.get('product_qty'),
                                'order_id': self.id,
                                'orderline_id': po_line_id.id,
                                'is_sent': False
                            }
                            history_lines.append(history_id)
                
                if line[0] == 2:  # delete line
                    po_line_id = self.env['purchase.order.line'].search([('id', '=', line[1])])
                    history_id = {
                        'product_id': po_line_id.product_id.id,
                        'name': po_line_id.name,
                        'product_uom': po_line_id.product_uom,
                        'prev_product_qty': po_line_id.prev_product_qty,
                        'product_qty': po_line_id.product_qty,
                        'order_id': po_line_id.order_id.id,
                        'is_unlink_line': True,
                        'is_sent': False
                    }
                    history_lines.append(history_id)
            
            if history_lines:
                self.history_data = history_lines
                self.is_po_updated = True
        return super(PurchaseOrder, self).write(values)
 
    @api.multi
    def action_rfq_send(self):
        '''
        Update -  Method intentionally overwritten to update the ctx in the mail compose wizard 
        and use this ctx in send_mail method overwritten below
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            else:
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        # code added by Abhay
        if 'send_rfq' in self.env.context:
            ctx['send_rfq_mail'] = True
        # Abhay Code ends here

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

class PurchaseOrderHistory(models.Model):
    _name = 'purchase.order.history'

    product_id = fields.Many2one('product.product', string='Product', ondelete='SET NULL')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    order_ids = fields.Many2one('purchase.order')
    name = fields.Text(string='Description')
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure')
    prev_product_qty = fields.Float(string='Previous Quantity', digits=dp.get_precision('Product Unit of Measure'))
    orderline_id = fields.Many2one('purchase.order.line')    
    is_sent = fields.Boolean("Email send", default=False)
    is_unlink_line = fields.Boolean("Deleted line", default=False)
    is_new_line = fields.Boolean("New line", default=False)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        context = self._context
        if context.get('active_model') and context.get('active_model')=='purchase.order' and context.get('send_rfq_mail'):
            data = self.env['purchase.order'].search([('id', 'in', context.get('active_ids'))])
            if data:
                for rec in data.history_data:
                    rec.is_sent = True
                    if rec.is_new_line:
                        rec.is_new_line = False
                data.write({'is_po_updated':False, 'is_supplier_notified':True})
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)