from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from openerp.exceptions import ValidationError

class QuickPPWizard(models.TransientModel):
    _name = 'quick.product.product.wiz'
    _description = 'Multi lines for products'

    product_id = fields.Many2one('product.product', string="Product")
    product_desc = fields.Char(string="Desc")
    lst_price = fields.Float(string="Unit Price")
    qty_to_process = fields.Float(string="Qty To Process")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    qty_available = fields.Float(string="Qty on hand")
    min_qty =  fields.Float(string="Min Qty")
    discount =  fields.Float(string="Discount")
    discount2 =  fields.Float(string="Discount2")
    discount3 =  fields.Float(string="Discount3")

    show_warn = fields.Boolean(default=False)
    quick_po_line_id = fields.Many2one('quick.po.line.wiz')

    @api.onchange('qty_to_process')
    def _onchange_quantity2process(self):
        date_order = datetime.strptime(self.env.context.get('date_order'), '%Y/%m/%d').date()
        partner_id = self.quick_po_line_id.partner_id
        company_id = self.env.context.get('company_id')
        supplier_info_ids = self.env['purchase.order'].search_product_supplier_info(company_id,partner_id.id, self.product_id.product_tmpl_id.id)

        is_vendor_price_applied = False
        for rec in supplier_info_ids:
            if rec.date_start and rec.date_start > date_order:
                continue
            if rec.date_end and rec.date_end < date_order:
                continue

            if  self.qty_to_process >= rec.min_qty:
                self.lst_price = rec.price or self.product_id.lst_price
                self.min_qty = rec.min_qty
                self.show_warn = False
                is_vendor_price_applied = True
                break

        if not is_vendor_price_applied:
            self.show_warn = True

class QuickPoLineWizard(models.TransientModel):
    _name = 'quick.po.line.wiz'
    _description = 'Add multi products in purchase order lines'

    partner_id = fields.Many2one('res.partner', string='Vendor')
    quick_product_ids = fields.One2many('quick.product.product.wiz', 'quick_po_line_id',string="Products")

    @api.multi
    def process(self):
        po_line_obj = self.env['purchase.order.line']
        
        order_id = self.env['purchase.order'].browse(self._context.get('active_id', False))
        for rec in self.quick_product_ids.filtered(lambda x: x.qty_to_process > 0):
            if rec.show_warn:
                raise ValidationError("Please correct the ordered quantities in the product lines shown as red.")
            
            product_cw_uom_qty = 0
            product_cw_uom = False
            if rec.product_id._is_cw_product():
                product_cw_uom = rec.product_id.cw_uom_id.id

                if rec.uom_id == rec.product_id.uom_id:
                    product_cw_uom_qty = rec.qty_to_process * rec.product_id.average_cw_quantity
                else:
                    product_uom_qty = rec.uom_id._compute_quantity(rec.qty_to_process, rec.product_id.uom_id)
                    product_cw_uom_qty = product_uom_qty * rec.product_id.average_cw_quantity

            if order_id.order_line and order_id.order_line.filtered(lambda x: x.product_id.id == rec.product_id.id):
                order_line_rec = order_id.order_line.filtered(lambda x: x.product_id.id == rec.product_id.id)
                if len(order_line_rec.ids) > 1:
                    order_line_rec = self.env['product.product'].browse(max(order_line_rec.ids))
                order_line_rec.product_qty = rec.qty_to_process
                order_line_rec.product_cw_uom_qty = product_cw_uom_qty
                order_line_rec.product_cw_uom = product_cw_uom
            else:
                taxes = rec.product_id.supplier_taxes_id
                fpos = order_id.fiscal_position_id
                taxes_id = fpos.map_tax(taxes, rec.product_id, order_id.partner_id) if fpos else taxes

                vals = {
                    'product_id': rec.product_id.id,
                    'name': rec.product_desc,
                    'product_uom': rec.product_id.uom_id.id,
                    'price_unit': rec.lst_price,
                    'product_qty': rec.qty_to_process,
                    'order_id': order_id.id,
                    'date_planned': order_id.date_planned,
                    'product_cw_uom_qty':product_cw_uom_qty,
                    'product_cw_uom': product_cw_uom,
                    'discount':rec.discount,
                    'discount2':rec.discount2,
                    'discount3':rec.discount3,
                }
                if taxes_id:
                    taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.env.context.get('company_id'))
                    vals['taxes_id'] =[(6, 0, taxes_id.ids)]

                res = po_line_obj.sudo().create(vals)
                res._onchange_quantity()
        return True