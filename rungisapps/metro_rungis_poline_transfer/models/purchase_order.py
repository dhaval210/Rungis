from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

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


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # @api.multi
    # def name_get(self):
    #     res = super().name_get()
    #     if self.env.context.get('wiz_po_name'):
    #         new_res = []
    #         for po_id,name in res:
    #             po = self.browse(po_id)
    #             name = _('%s %s %s') % (po.display_name, po.partner_id.name, po.po_date_planned)
    #             new_res.append((po.id,name))
    #         return new_res
    #     return res

    @api.multi
    def action_po_line_wiz_update_orderid(self):
        view = self.env.ref('metro_rungis_poline_transfer.form_po_line_transfer_wiz')
        line_ids_vals = []
        for rec in self.order_line:
            vals = {
                'product_id': rec.product_id.id,
                'product_desc' : rec.name,
                'vendor_id' : self.partner_id.id,
                'product_qty' : rec.product_qty,
                'uom_id' : rec.product_uom.id,
                'order_id' : self.id,
                'order_line_id' : rec.id,
            }
            line_ids_vals.append([0,0,vals])
        wiz = self.env['po.line.transfer.wiz'].create({'po_id': self.id, 'line_ids' : line_ids_vals})
        ctx = dict(self._context)
        return {
                'name': _('Move PO Line'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'po.line.transfer.wiz',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': ctx,
            }


