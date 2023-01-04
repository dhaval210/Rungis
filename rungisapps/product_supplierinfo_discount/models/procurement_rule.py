"""inheriting procurement rule"""
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class ProcurementRule(models.Model):
    """rule can be applied here eg:purchase order will created while creating sale order"""
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        cache = {}
        suppliers = product_id.seller_ids \
            .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (
                not r.product_id or r.product_id == product_id))
        if not suppliers:
            msg = ('There is no vendor associated to the product %s.'
                   'Please define a vendor for this product.') % (product_id.display_name,)
            raise UserError(msg)

        supplier = self._make_po_select_supplier(values, suppliers)
        partner = supplier.name

        domain = self._make_po_get_domain(values, partner)
        if domain in cache:
            po = cache[domain]
        else:
            po = self.env['purchase.order'].sudo().search([dom for dom in domain])
            po = po[0] if po else False
            cache[domain] = po
        if not po:
            vals = self._prepare_purchase_order(product_id, product_qty,
                                                product_uom, origin, values, partner)
            po = self.env['purchase.order'].sudo().create(vals)
            cache[domain] = po
        elif not po.origin or origin not in po.origin.split(', '):
            if po.origin:
                if origin:
                    po.write({'origin': po.origin + ', ' + origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': origin})

        po_line = False
        if not po_line:
            vals = self._prepare_purchase_order_line(product_id, product_qty,
                                                     product_uom, values, po, supplier)
            self.env['purchase.order.line'].sudo().create(vals)

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty,
                                     product_uom, values, po, partner):
        procurement_uom_po_qty = product_uom.compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id.select_seller(
            partner_id=partner.name,
            quantity=procurement_uom_po_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id)

        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == values['company_id'].id)

        price_unit = self.env['account.tax'].\
            fix_tax_included_price_company(seller.price, product_id.supplier_taxes_id,
                                           taxes_id, values['company_id']) if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        product_lang = product_id.with_context({
            'lang': partner.name.lang,
            'partner_id': partner.name.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = self.env['purchase.order.line']._get_date_planned(seller, po=po).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        if values.get('sale_line_id'):
            line = self.env['sale.order.line'].browse(values.get('sale_line_id'))
            name = line.name
        if values.get('move_dest_ids'):
            name = values['move_dest_ids'].sale_line_id.name
        return {
            'name': name,
            'product_qty': procurement_uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'orderpoint_id': values.get('orderpoint_id', False) and values.get('orderpoint_id').id,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,
            'discount': seller.discount,
            'move_dest_ids': [(4, x.id) for x in values.get('move_dest_ids', [])],
        }
