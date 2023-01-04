from odoo import fields, models


class CacheOrderGrid(models.Model):
    _inherit = 'cache.order.grid'

    incoming_vendor_confirmed_qty = fields.Float(help="incoming qty of PO in confirmed state for the specific vendor")
    incoming_vendor_planned_qty = fields.Float(help="incoming qty of PO in RFQ state for the specific vendor")
    incoming_confirmed_qty = fields.Float(help="sum of incoming qty of POs in confirmed for all vendor")
    incoming_planned_qty = fields.Float(help="sum of incoming qty of PO in RFQ state for all vendor")

    def sum_daily_diff(self, data):
        sum = super().sum_daily_diff(data)
        sum += data['incoming_confirmed_qty'] + data['incoming_planned_qty']
        return sum

    def get_sum_daily_purchase_line_qty(self, single_date, data, warehouse):
        vendor_id = data['vendor_id']
        product_id = data['tmp_product_id']

        today = single_date.strftime('%Y-%m-%d ' + '00:00:00')
        tomorrow = single_date.strftime('%Y-%m-%d ' + '23:59:59')

        po_data = self.env['purchase.order'].search_read([
            # ('partner_id', '=', vendor_id),
            ('picking_type_id', '=', warehouse.receipt_in_id.id),
            ('date_planned', '>=', today),
            ('date_planned', '<=', tomorrow)
        ], ['id'])
        # po_vendor_data = po_data.filtered(lambda x: x.partner_id == vendor_id)
        po_vendor_data = self.env['purchase.order'].search_read([
            ('partner_id', '=', vendor_id),
            ('picking_type_id', '=', warehouse.receipt_in_id.id),
            ('date_planned', '>=', today),
            ('date_planned', '<=', tomorrow)
        ], ['id'])

        po_ids = [p['id'] for p in po_data]
        po_vendor_ids = [pv['id'] for pv in po_vendor_data]
        pol_data = self.env['purchase.order.line'].search([
            ('product_id', '=', product_id),
            ('order_id', 'in', po_ids),
            ('date_planned', '>=', today),
            ('date_planned', '<=', tomorrow),
        ])
        pol_vendor_data = self.env['purchase.order.line'].search([
            ('product_id', '=', product_id),
            ('order_id', 'in', po_vendor_ids),
            ('date_planned', '>=', today),
            ('date_planned', '<=', tomorrow),
        ])
        if len(pol_data) > 0:
            purchase_data = pol_data.filtered(lambda x: x.state == 'purchase')
            rfq_data = pol_data.filtered(lambda x: x.state in ['draft', 'sent', 'to approve'])
            purchase_data_vendor = pol_vendor_data.filtered(lambda x: x.state == 'purchase')
            rfq_data_vendor = pol_vendor_data.filtered(lambda x: x.state in ['draft', 'sent', 'to approve'])


            confirmed_qty = sum(purchase_data.mapped('product_qty'))
            planned_qty = sum(rfq_data.mapped('product_qty'))
            confirmed_qty_vendor = sum(purchase_data_vendor.mapped('product_qty'))
            planned_qty_vendor = sum(rfq_data_vendor.mapped('product_qty'))

            data.update({
                'incoming_vendor_confirmed_qty': confirmed_qty_vendor,
                'incoming_vendor_planned_qty': planned_qty_vendor,
                'incoming_confirmed_qty': confirmed_qty,
                'incoming_planned_qty': planned_qty,
            })
        else:
            data.update({
                'incoming_vendor_confirmed_qty': 0,
                'incoming_vendor_planned_qty': 0,
                'incoming_confirmed_qty': 0,
                'incoming_planned_qty': 0,
            })
        return data

    def add_addition_vendor_or_product_data(self, supplier, data={}, warehouse=False):
        data = super().add_addition_vendor_or_product_data(supplier, data, warehouse)
        # do magic here
        data.update({
            'tmp_product_id': supplier.product_tmpl_id.product_variant_id.id
        })
        return data

    def add_addition_date_data(self, single_date, data, warehouse):
        data = super().add_addition_date_data(single_date, data, warehouse)
        # do magic here
        data.update(self.get_sum_daily_purchase_line_qty(single_date, data, warehouse))
        return data
