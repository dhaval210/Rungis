from odoo import fields, models
from datetime import timedelta


class CacheOrderGrid(models.Model):
    _name = 'cache.order.grid'
    _description = 'Order Grid Cache'

    DAYS_PAST = 5
    DAYS_FUTURE = 20

    vendor_id = fields.Many2one(comodel_name='res.partner', index=True)
    product_tmpl_id = fields.Many2one(comodel_name='product.template')
    product_id = fields.Many2one(
        comodel_name='product.product',
        related='product_tmpl_id.product_variant_id',
        store=True, index=True
    )
    date = fields.Date(help="date of the data entry", index=True)
    in_past = fields.Boolean(help="indicates if the data is in the past (outdated)")
    daily_qty_diff = fields.Float(help="diff of incoming to outgoing qty, used for daily on hand computation")

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def sum_daily_diff(self, data):
        return 0

    def add_addition_vendor_or_product_data(self, supplier, data={}, warehouse=False):
        # this is called once per supplier/product
        # possibility to extend vendor or product based data
        # in extending modules
        data.update({
            'vendor_id': supplier.name.id,
            'product_tmpl_id': supplier.product_tmpl_id.id,
        })
        return data

    def add_addition_date_data(self, single_date, data, warehouse):
        # this is called for every single date
        # possibility to extend date based data in extending modules
        in_past = False
        if single_date < fields.Date.today():
            in_past = True
        data.update({
            'date': single_date,
            'in_past': in_past,
        })

        return data

    def populate_cache_order_grid(self):
        supplier_infos = self.env['product.supplierinfo'].search([])
        start_date = fields.Date.today() - timedelta(self.DAYS_PAST)
        end_date = fields.Date.today() + timedelta(self.DAYS_FUTURE)

        for supplier in supplier_infos:
            data = {}
            product_template_id = supplier.product_tmpl_id.id
            existing_data = self.search_read([
                ('vendor_id', '=', supplier.name.id),
                ('product_tmpl_id', '=', product_template_id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ], ['id', 'date'])
            if len(existing_data) == (self.DAYS_PAST + self.DAYS_FUTURE):
                continue
            existing_dates = [ed['date'] for ed in existing_data]
            data.update(self.add_addition_vendor_or_product_data(supplier, data))
            for single_date in self.daterange(start_date, end_date):
                if single_date in existing_dates:
                    continue
                data.update(self.add_addition_date_data(single_date, data))
                data.update({'daily_qty_diff': self.sum_daily_diff(data)})
                self.create(data)
        return True
