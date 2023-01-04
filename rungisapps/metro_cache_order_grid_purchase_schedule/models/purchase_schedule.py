from odoo import models, fields


class Schedule(models.Model):
    _inherit = 'purchase.schedule'

    # TODO
    # def create(self, vals_list):
    # res = super().create(vals_list)
    # do reset
    # return res

    def write(self, values):
        res = super().write(values)

        for rec in self:
            # do this as async job
            # rec.with_delay().reset_cache_dates(rec, values)
            rec.reset_cache_dates(rec, values)
        return res

    # @job(default_channel='root.cache_order_grid')
    def reset_cache_dates(self, rec, values):
        CacheGrid = self.env['cache.order.grid']
        if 'order_deadline' in values or 'delivery_lead_time' in values:
            data = {}
            if rec.partner_id is not False:
                # get schedule days (integer)
                data = CacheGrid.get_data_with_integer_day_order_delivery(
                    rec.partner_id.schedule_ids,
                    data
                )
                # load all cache data for vendor_id
                cache_data = CacheGrid.search([
                    ('vendor_id', '=', rec.partner_id.id),
                    ('date', '>=', fields.Date.today())
                ])
                for cd in cache_data:
                    # rewrite days
                    data = CacheGrid.get_data_with_check_order_delivery_date(
                        cd.date,
                        data
                    )
                    cd.write(data)
