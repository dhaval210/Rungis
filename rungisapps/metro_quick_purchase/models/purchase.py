from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from openerp.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def search_product_supplier_info(self,company_id,partner_id,product_tmpl_id=False):
        if product_tmpl_id:
            product_supplierinfo_ids = self.env['product.supplierinfo'].search([
                ('product_tmpl_id.purchase_ok', '=', True ),
                ('company_id', '=', company_id),
                ('name','=',partner_id), 
                ('product_tmpl_id', '=', product_tmpl_id )]
                ).sorted(lambda s: (s.sequence))

        else:
            product_supplierinfo_ids = self.env['product.supplierinfo'].search([
                ('product_tmpl_id.purchase_ok', '=', True ),
                ('company_id', '=', company_id),
                ('name','=',partner_id)]
                ).sorted(lambda s: (s.sequence))
        return product_supplierinfo_ids

    @api.multi
    def action_select_products(self):
        view = self.env.ref('metro_quick_purchase.form_quick_po_line_wiz')

        if not self.partner_id:
            raise ValidationError(_("Please select the vendor."))

        date_order = self.date_order.date()
        product_supplierinfo_ids = self.search_product_supplier_info(self.company_id.id,self.partner_id.id)
        
        quick_po_line_vals = []
        product_tmpl_ids = []
        for rec in product_supplierinfo_ids:
            if rec.date_start and rec.date_start > date_order:
                continue
            if rec.date_end and rec.date_end < date_order:
                continue

            vals = {}
            if not  rec.product_tmpl_id in product_tmpl_ids:
                product_id  = None
                if rec.product_id:
                    product_id = rec.product_id
                else:
                    product_id = rec.product_tmpl_id.product_variant_ids[0]

                product_desc = ''
                
                if rec.product_code:
                    product_desc += '[' + str(rec.product_code) + '] '
                elif product_id.default_code:
                    product_desc += '[' + str(product_id.default_code) + '] '

                if rec.product_name:
                    product_desc += rec.product_name
                elif product_id.name:
                    product_desc += product_id.name

                if not product_desc:
                    product_desc = product_id.display_name

                vals = {
                        'product_id' : product_id.id,
                        'product_desc' : product_desc,
                        'lst_price' : rec.price or 0,
                        'qty_to_process' : 0,
                        'uom_id': rec.product_uom.id,
                        'qty_available' : product_id.qty_available,
                        'min_qty' : rec.min_qty or 0,
                        'discount' : rec.discount or 0,
                        'discount2' : rec.discount2 or 0,
                        'discount3' : rec.discount3 or 0,
                    } 
                
                product_tmpl_ids.append(rec.product_tmpl_id)
                quick_po_line_vals.append([0,0,vals])
            
            else:
                product_id = None
                if rec.product_id:
                    product_id = rec.product_id
                else:
                    product_id = rec.product_tmpl_id.product_variant_ids[0]

                product_desc = ''
                if rec.product_code:
                    product_desc += '[' + str(rec.product_code) + '] ' 
                elif product_id.default_code:
                    product_desc += '[' + str(product_id.default_code) + '] ' 

                if rec.product_name:
                    product_desc += rec.product_name
                elif  product_id.name:
                    product_desc += product_id.name

                if not product_desc:
                    product_desc = product_id.display_name


                for quick_po_rec in quick_po_line_vals:
                    pt_id = quick_po_rec[2]
                    if pt_id['product_id'] == product_id.id and pt_id['lst_price']>rec.price:
                        pt_id['lst_price'] = rec.price
                        pt_id['min_qty'] = rec.min_qty
                        pt_id['product_desc'] = product_desc
                        pt_id['discount'] = rec.discount or 0
                        pt_id['discount2'] = rec.discount2 or 0
                        pt_id['discount3'] = rec.discount3 or 0

        wiz = self.env['quick.po.line.wiz'].create({
                    'partner_id': self.partner_id.id, 
                    'quick_product_ids' : quick_po_line_vals})

        ctx = dict(self._context,
            partner_id = self.partner_id.id,
            date_order= self.date_order.strftime("%Y/%m/%d"),
            company_id = self.company_id.id,
            )

        return {
                'name': _('Quick Purchase'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'quick.po.line.wiz',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': ctx,
            }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def open_packaging_info(self):
        product_packaging_ids = self.env['product.packaging'].search([('product_id', '=', self.product_id.id)])
        action = self.env.ref('product.action_packaging_view').read()[0]
        if len(product_packaging_ids) > 1:
            action['domain'] = [('id', 'in', product_packaging_ids.ids)]
        elif len(product_packaging_ids) == 1:
            action['views'] = [(self.env.ref('product.product_packaging_form_view').id, 'form')]
            action['res_id'] = product_packaging_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action