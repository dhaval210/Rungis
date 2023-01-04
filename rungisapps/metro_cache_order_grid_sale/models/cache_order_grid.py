from odoo import fields, models
from datetime import timedelta


class CacheOrderGrid(models.Model):
    _inherit = 'cache.order.grid'

    outgoing_confirmed_qty = fields.Float(help="displays the amount of sold (SO) qty")
    outgoing_demand_qty = fields.Float(help="displays the amount of the sales demand (softm only)")
    outgoing_planned_qty = fields.Float(help="displays the amount of the quotations (draft) qty")

    def recompute_line_qty(self):
        for rec in self:
            data = {}
            data['tmp_product_id'] = rec.product_id.id
            data['outgoing_confirmed_qty'] = 0
            data['outgoing_demand_qty'] = 0
            data['outgoing_planned_qty'] = 0
            data = self.get_sum_daily_sale_line_qty(rec.date, data, rec.warehouse_id)
            rec.write(data)

    def get_sum_daily_sale_line_qty(self, single_date, data, warehouse):
        product_id = data['tmp_product_id']

        # + 1 day
        today = (single_date + timedelta(days=1)).strftime('%Y-%m-%d ' + '00:00:00')
        tomorrow = (single_date + timedelta(days=1)).strftime('%Y-%m-%d ' + '23:59:59')
        outgoing_planned_qty = 0
        confirmed_qty = 0
        outgoing_demand_qty = 0

        draft_so_data = self.env['sale.order'].search_read([
            ('warehouse_id', '=', warehouse.id),
            ('commitment_date', '>=', today),
            ('commitment_date', '<=', tomorrow),
            ('state', 'in', ['draft', 'sent'])
        ], ['id'])
        sale_so_data = self.env['sale.order'].search_read([
            ('warehouse_id', '=', warehouse.id),
            ('commitment_date', '>=', today),
            ('commitment_date', '<=', tomorrow),
            ('state', '=', 'sale')
        ], ['id'])

        # new
        draft_so_ids = [dsd['id'] for dsd in draft_so_data]
        sol_data = self.env['sale.order.line'].search([
            ('product_id', '=', product_id),
            ('order_id', 'in', draft_so_ids),
        ])
        if len(sol_data) > 0:
            for sol in sol_data:
                outgoing_demand_qty += sol.demand_qty
                if sol.demand_qty > sol.product_uom_qty:
                    outgoing_planned_qty += sol.demand_qty
                else:
                    outgoing_planned_qty += sol.product_uom_qty

        sale_so_ids = [ssd['id'] for ssd in sale_so_data]
        sol_data = self.env['sale.order.line'].search_read([
            ('product_id', '=', product_id),
            ('order_id', 'in', sale_so_ids),
        ], ['product_uom_qty'])
        if len(sol_data) > 0:
            confirmed_qty = sum([sd['product_uom_qty'] for sd in sol_data])

        data.update({
            'outgoing_confirmed_qty': confirmed_qty,
            'outgoing_demand_qty': outgoing_demand_qty,
            'outgoing_planned_qty': outgoing_planned_qty,
        })

        return data

    def sum_daily_diff(self, data):
        sum = super().sum_daily_diff(data)
        sum = sum - data['outgoing_planned_qty'] - data['outgoing_confirmed_qty']
        return sum

    def add_addition_vendor_or_product_data(self, supplier, data={}, warehouse=False):
        data = super().add_addition_vendor_or_product_data(supplier, data, warehouse)
        data.update({
            'tmp_product_id': supplier.product_tmpl_id.product_variant_id.id
        })
        return data

    def add_addition_date_data(self, single_date, data, warehouse):
        data = super().add_addition_date_data(single_date, data, warehouse)
        data.update(self.get_sum_daily_sale_line_qty(single_date, data, warehouse.warehouse_id))
        return data
