from odoo import models, fields
from odoo.addons.queue_job.job import job
from datetime import date, timedelta, datetime
import ast


class CacheOrderGrid(models.Model):
    _inherit = 'cache.order.grid'

    min_qty = fields.Float(help="min qty of reordering rule")
    max_qty = fields.Float(help="max qty of reordering rule")
    transit_in_qty = fields.Float(help="incoming transit qty based on order grid configuration")
    transit_out_qty = fields.Float(help="outcoming transit qty based on order grid configuration")
    removal_qty = fields.Float(help="displays the amount of qty of expired lots")
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', index=True)
    qty_on_hand = fields.Float(help="qty on hand based on incoming & outgoing qtys")

    def sum_daily_diff(self, data):
        sum = super().sum_daily_diff(data)
        sum = sum - data['transit_out_qty'] + data['transit_in_qty']
        if (
            'outgoing_planned_qty' in data and
            'outgoing_confirmed_qty' in data and
            (data['outgoing_planned_qty'] + data['outgoing_confirmed_qty']) < data['removal_qty']
        ):
            sum = sum - (data['removal_qty'] - data['outgoing_planned_qty'] - data['outgoing_confirmed_qty'])
        return sum

    def get_removal_qty_from_lot(self, single_date, data, warehouse):
        lots = self.env['stock.production.lot'].search_read([
            ('life_date', '>=', single_date.strftime('%Y-%m-%d ' + '00:00:00')),
            ('life_date', '<=', single_date.strftime('%Y-%m-%d ' + '23:59:59')),
            ('product_id', '=', data['tmp_product_id']),
        ], ['id'])

        removal_qty = 0
        if len(lots) > 0:
            quants = self.env["stock.quant"].search([
                ('location_id', 'child_of', warehouse.warehouse_id.lot_stock_id.id),
                ('lot_id', 'in', [l['id'] for l in lots])
            ])
            if len(quants) > 0:
                removal_qty = sum([q['quantity'] for q in quants if q['quantity'] > 0])
        data.update({
            'removal_qty': removal_qty
        })
        return data

    def check_onhand_grid(self, product_template_id, warehouse):
        cpqg = self.env['cache.product.qty.grid'].search([
            ('warehouse_id', '=', warehouse.id),
            ('product_tmpl_id', '=', product_template_id),
        ], limit=1)
        if cpqg.id is False:
            self.env['cache.product.qty.grid'].create({
                'warehouse_id': warehouse.id,
                'product_tmpl_id': product_template_id
            })
        return True

    def get_transit_qty(self, single_date, operation_ids, product):
        something = 0
        moves = self.env['stock.move'].search_read([
            ('picking_type_id', 'in', operation_ids),
            ('date_expected', '>=', single_date.strftime('%Y-%m-%d ' + '00:00:00')),
            ('date_expected', '<=', single_date.strftime('%Y-%m-%d ' + '23:59:59')),
            ('state', 'not in', ['draft', 'cancel', 'done']),
            ('product_id', '=', product)
        ], ['product_uom_qty'])
        something = sum([m['product_uom_qty'] for m in moves])
        return something

    def get_transit_data(self, single_date, data, warehouse):
        data.update({
            'transit_in_qty': self.get_transit_qty(single_date, warehouse.transit_in_ids.ids, data['tmp_product_id']),
            'transit_out_qty': self.get_transit_qty(single_date, warehouse.transit_out_ids.ids, data['tmp_product_id']),
        })
        return data

    def add_addition_warehouse_data(self, warehouse, data={}):
        return data

    def add_addition_vendor_or_product_data(self, supplier, data={}, warehouse=False):
        data = super().add_addition_vendor_or_product_data(supplier, data, warehouse)
        orderpoint = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', supplier.product_tmpl_id.product_variant_id.id),
            ('warehouse_id', '=', warehouse.warehouse_id.id)
        ], limit=1)
        if len(orderpoint) > 0:
            data.update({
                'min_qty': orderpoint.product_min_qty,
                'max_qty': orderpoint.product_max_qty,
            })
        elif supplier.min_qty > 0:
            data.update({
                'min_qty': supplier.min_qty,
                'max_qty': supplier.min_qty,
            })
        data.update({
            'warehouse_id': warehouse.warehouse_id.id,
            'tmp_product_id': supplier.product_tmpl_id.product_variant_id.id
        })
        return data

    def add_addition_date_data(self, single_date, data, warehouse):
        data = super().add_addition_date_data(single_date, data, warehouse)
        data = self.get_removal_qty_from_lot(single_date, data, warehouse)
        data = self.get_transit_data(single_date, data, warehouse)
        return data

    @job(default_channel='root.order_grid.populate_warehouse')
    def job_populate_warehouse(self, whid, supplier=False, product=False, force_update=False, start_date=False, end_date=False, company_id=False):
        domain = []
        if supplier is not False:
            domain += [('name', '=', supplier)]
        if product is not False:
            pid = self.env['product.template'].search([('default_code', '=', product)], limit=1)
            if pid.id is not False:
                domain += [('product_tmpl_id', '=', pid.id)]
        if company_id is not False:
            domain += [('company_id', '=', company_id)]
        supplier_infos = self.env['product.supplierinfo'].search(domain)

        data = {}
        data.update(self.add_addition_warehouse_data(whid, data))
        for supp in supplier_infos:
            wh_name = whid.warehouse_id.name
            prod_name = supp.product_tmpl_id.name
            sup_name = supp.name.name
            job_desc = wh_name + ' ' + sup_name + ' ' + prod_name
            self.with_delay(description=job_desc).job_populate_supplier(supp, whid, data, force_update, start_date, end_date)

        return True

    @job(default_channel='root.order_grid.populate_supplier')
    def job_populate_supplier(self, supplier, whid, data, force_update=False, start_date=False, end_date=False):
        if start_date is False:
            start_date = fields.Date.today() - timedelta(self.DAYS_PAST)
        if end_date is False:
            end_date = fields.Date.today() + timedelta(self.DAYS_FUTURE)
        qty_on_hand = 0
        product_template_id = supplier.product_tmpl_id.id
        # if product_template_id not in checked_templates:
        self.check_onhand_grid(product_template_id, whid.warehouse_id)
        existing_data = self.search_read([
            ('vendor_id', '=', supplier.name.id),
            ('product_tmpl_id', '=', product_template_id),
            ('warehouse_id', '=', whid.warehouse_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ], ['id', 'date'])
        if (
            len(existing_data) == (self.DAYS_PAST + self.DAYS_FUTURE) and
            force_update is False
        ):
            return
        # existing_dates = existing_data.mapped('date')
        existing_dates = [ed['date'] for ed in existing_data]
        data.update(self.add_addition_vendor_or_product_data(supplier, data, whid))
        for single_date in self.daterange(start_date, end_date):
            if force_update is False and single_date in existing_dates:
                continue
            if (
                single_date in existing_dates and
                single_date < fields.Date.today()
            ):
                continue
            data.update(self.add_addition_date_data(single_date, data, whid))
            data.update({'daily_qty_diff': self.sum_daily_diff(data)})
            if single_date == fields.Date.today():
                # cache.product.qty.grid
                on_hand = self.env['cache.product.qty.grid'].search([
                    ('product_id', '=', data['tmp_product_id']),
                    ('warehouse_id', '=', whid.warehouse_id.id)
                ], limit=1)
                if on_hand.id is not False:
                    qty_on_hand = on_hand.qty_on_hand + data['daily_qty_diff']
            elif single_date > fields.Date.today():
                qty_on_hand += data['daily_qty_diff']
            data.update({'qty_on_hand': qty_on_hand})
            if single_date in existing_dates:
                for ed in existing_data:
                    if ed['date'] == single_date:
                        eduid = self.browse(ed['id'])
                        eduid.write(data)
                        break
            else:
                self.create(data)

    def populate_cache_order_grid(self, supplier=False, product=False, force_update=False, start_date=False, end_date=False, company_id=False):
        # examples
        # create new entries only
        # model.populate_cache_order_grid()

        # update all
        # model.populate_cache_order_grid(force_update=True)

        # update specific vendor
        # model.populate_cache_order_grid(supplier='Valerie Melton', force_update=True)

        # update specific product
        # model.populate_cache_order_grid(product='41286', force_update=True)

        # update specific product for specific vendor
        # model.populate_cache_order_grid(supplier='Valerie Melton', product='41286', force_update=True)

        # update specific product for specific vendor in a specific date range
        # model.populate_cache_order_grid(supplier='Valerie Melton', product='41286', force_update=True, start_date="2022-01-01", end_date="2022-05-01")
        if start_date is not False:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = fields.Date.today() - timedelta(self.DAYS_PAST)
        if end_date is not False:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = fields.Date.today() + timedelta(self.DAYS_FUTURE)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        generic_warehouse_ids = get_param('metro_cache_order_grid_stock.res_generic_warehouse_ids')
        generic_warehouse = self.env['res.generic.warehouse'].browse(
            ast.literal_eval(generic_warehouse_ids)
        )
        for whid in generic_warehouse:
            wh_name = whid.warehouse_id.name
            job_desc = wh_name + ' populate grid data'
            self.with_delay(description=job_desc).job_populate_warehouse(whid, supplier, product, force_update, start_date, end_date, company_id)
        return True
