from odoo import fields, models


class CacheOrderGrid(models.Model):
    _inherit = 'cache.order.grid'

    is_delivery_date = fields.Boolean(help="indicates if this date is a delivery day, based on purchase schedule in contact")
    is_order_date = fields.Boolean(help="indicates if this date is an order day, based on purchase schedule in contact")

    def get_data_with_integer_day_order_delivery(self, schedule_ids, data):
        delivery_days = []
        order_days = []
        for schedule in schedule_ids:
            order_days += [int(schedule.order_deadline)]
            lead_time = int(schedule.order_deadline) + schedule.delivery_lead_time
            if lead_time > 6:
                lead_time -= 7
            delivery_days += [lead_time]
        data.update({
            'order_days': order_days,
            'delivery_days': delivery_days,
        })
        return data

    def get_data_with_check_order_delivery_date(self, single_date, data):
        # this requires get_data_with_integer_day_order_delivery
        # to be called first
        is_order = False
        is_delivery = False
        if single_date.weekday() in data['order_days']:
            is_order = True
        if single_date.weekday() in data['delivery_days']:
            is_delivery = True
        data.update({
            'is_delivery_date': is_delivery,
            'is_order_date': is_order,
        })
        return data

    def add_addition_vendor_or_product_data(self, supplier, data={}, warehouse=False):
        data = super().add_addition_vendor_or_product_data(supplier, data, warehouse)
        data.update(self.get_data_with_integer_day_order_delivery(
            supplier.name.schedule_ids,
            data
        ))
        return data

    def add_addition_date_data(self, single_date, data, warehouse):
        data = super().add_addition_date_data(single_date, data, warehouse)
        data.update(self.get_data_with_check_order_delivery_date(single_date, data))
        return data
