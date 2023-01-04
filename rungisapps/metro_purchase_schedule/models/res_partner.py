# -*- encoding: utf-8 -*-
import ast

import pytz
from odoo import models, fields, api, _
from datetime import timedelta, datetime, date

from odoo.exceptions import UserError


class PurchaseSchedule(models.Model):
    _name = "purchase.schedule"
    _description = "Purchase Schedule"

    name = fields.Char(string="Name")
    order_deadline = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Order day of week', required=True, index=True, default='0')
    time = fields.Float(digits=(12, 2), required=True, string="Order Cut off time")
    delivery_lead_time = fields.Integer(string="Lead time(Days)")
    partner_id = fields.Many2one(
        'res.partner', 'Purchase Schedule', index=True, ondelete='cascade')
    order_date = fields.Datetime(string="Order Date", readonly=True)
    expire_date = fields.Date(string="Expire Date")
    last_update = fields.Integer("Last Update", readonly=True)

    def get_working_day(self, calendar_id, input_date):
        """
        Function returns the day count need to add to get
        working day.
        """

        leave_ids = self.env['resource.calendar.leaves'].search([('calendar_id', '=', calendar_id)])
        for leave in leave_ids:

            leave_date_from = leave.date_from.date()
            leave_date_to = leave.date_to.date()
            if leave_date_from <= input_date <= leave_date_to:
                return 1
        return 0

    def get_worktime(self, calendar_id, time):
        """
        return the work time scheduled between
        the factory calendar work time.
        """

        work_from = calendar_id.attendance_ids.mapped('hour_from')
        work_to = calendar_id.attendance_ids.mapped('hour_to')
        if work_from and work_to:
            min_time = min(work_from)
            max_time = max(work_to)
            if time < min_time:
                time = min_time
            elif time > max_time:
                time = max_time
        return time

    def get_timezone_date(self, date):
        """
        return date adjusted based on
        user timezone.
        """
        user_tz = pytz.timezone(self.env.user.tz or self.env.context.get('tz')) if self.env.user.tz or self.env.context.get('tz') else False
        if user_tz:
            test_date = pytz.utc.localize(datetime.now()).astimezone(user_tz)
            time_diff = test_date.utcoffset()
            order_date = date - time_diff
            return order_date
        else:
            return date

    def create(self, vals_list):
        """
        supered for checking valid values when creating
        record and calculate order date
        """

        schedule_ids = self.env['purchase.schedule'].search([('partner_id', '=',
                                                              vals_list[0]['partner_id'])])
        week_days = schedule_ids.mapped('order_deadline')
        partner_id = self.env['res.partner'].browse([vals_list[0]['partner_id']])
        calendar_id = partner_id.factory_calendar_id
        weekdays = [int(vals['order_deadline']) for vals in vals_list]
        if len(weekdays) != len(set(weekdays)):
            raise UserError(_("The weekdays having duplicates."))
        for vals in vals_list:
            if vals['time'] >= 24:
                raise UserError(_("The Time is not valid, it needs to be under 24:00"))
            if vals['order_deadline'] in week_days:
                raise UserError(_("This weekday is used, change the weekday."))
            if calendar_id:
                work_weeks = calendar_id.attendance_ids.mapped('dayofweek')
                if vals['order_deadline'] not in work_weeks:
                    raise UserError(_("This weekday is not a working day."))
            if vals['delivery_lead_time'] > 365:
                raise UserError(_("This lead time is not valid, it should be under 365"))
        res = super(PurchaseSchedule, self).create(vals_list)
        for recd in res:
            next_date = date.today() + timedelta(
                (int(recd.order_deadline) - date.today().weekday()) % 7)
            use_time = self.get_worktime(calendar_id, recd.time) if calendar_id else recd.time
            float_value = use_time - int(use_time)

            flag = True
            while flag:
                if recd.partner_id.factory_calendar_id:
                    calendar_id = recd.partner_id.factory_calendar_id
                    status = self.get_working_day(calendar_id.id, next_date)
                    if status != 0:
                        next_date = next_date + timedelta(days=status)
                    else:
                        flag = False
                else:
                    flag = False
            order_date = datetime(next_date.year, next_date.month, next_date.day, int(use_time), 0)

            duration = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.schedule_duration',
                                                                        default=False)
            tags = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.tags', default=False)
            order_date = order_date + timedelta(hours=float_value)
            stop_date = order_date + timedelta(minutes=int(duration))
            order_date = self.get_timezone_date(order_date)
            stop_date = self.get_timezone_date(stop_date)
            buyer_ids = recd.partner_id.buyer_id.partner_id.ids if recd.partner_id.buyer_id else []
            vals = {
                'name': "Order " + recd.partner_id.name,
                'start': order_date,
                'stop': stop_date,
                'categ_ids': [(6, 0, ast.literal_eval(str(tags)))] if tags else False,
                'schedule_id': recd.id,
                'partner_ids': [(6, 0, ast.literal_eval(str(buyer_ids)))]
            }
            calendar_obj = self.env['calendar.event']
            calendar_obj.sudo().create(vals)
            recd.order_date = order_date
            recd.expire_date = order_date.date() + timedelta(days=90)

        return res

    def write(self, vals):
        """supered for checking valid
        values when writing
        record and calculate order date on changes"""

        schedule_ids = self.env['purchase.schedule'].search([('partner_id', '=',
                                                              self.partner_id.id)])
        week_days = schedule_ids.mapped('order_deadline')
        calendar_id = self.env['calendar.event'].search([('schedule_id', '=', self.id)])
        flag = False
        partner_calendar_id = self.partner_id.factory_calendar_id
        if 'time' in vals.keys():
            flag = True
            if vals['time'] >= 24:
                raise UserError(_("The Time is not valid, it needs to be under 24:00"))
            for calendar in calendar_id:
                use_time = self.get_worktime(partner_calendar_id, vals['time']) if calendar else vals['time']
                float_value = use_time - int(use_time)
                prev_date = calendar.start
                next_date = datetime(prev_date.year, prev_date.month, prev_date.day, int(use_time))
                next_date = next_date + timedelta(hours=float_value)
                duration = calendar.duration - int(calendar.duration)
                stop_date = next_date + timedelta(hours=duration)
                next_date = self.get_timezone_date(next_date)
                stop_date = self.get_timezone_date(stop_date)
                calendar.stop = stop_date
                calendar.start = next_date
                self.order_date = next_date
                self.expire_date = next_date.date() + timedelta(days=90)

        if 'order_deadline' in vals.keys():
            if vals['order_deadline'] in week_days:
                raise UserError(_("This weekday is used, change the weekday."))
            if partner_calendar_id:
                work_weeks = partner_calendar_id.attendance_ids.mapped('dayofweek')
                if vals['order_deadline'] not in work_weeks:
                    raise UserError(_("This weekday is not a working day."))
            next_date = date.today() + timedelta(
                (int(vals['order_deadline']) - date.today().weekday()) % 7)

            flag_day = True
            while flag_day:
                if self.partner_id.factory_calendar_id:
                    partner_calendar_id = self.partner_id.factory_calendar_id
                    status = self.get_working_day(partner_calendar_id.id, next_date)
                    if status != 0:
                        next_date = next_date + timedelta(days=status)
                    else:
                        flag_day = False
                else:
                    flag_day = False
            prev_calendar_ids = False
            if len(calendar_id) > 1:
                dates = calendar_id.mapped('start')
                min_date = min(dates)
                prev_calendar_ids = calendar_id.filtered(lambda c: c.start != min_date)
                calendar_id = calendar_id.filtered(lambda c: c.start == min_date)
            time = self.time if not flag else vals['time']
            use_time = self.get_worktime(partner_calendar_id, time) if calendar_id else time
            float_value = use_time - int(use_time)
            next_date = datetime(next_date.year, next_date.month, next_date.day, int(use_time))
            next_date = next_date + timedelta(hours=float_value)
            duration = calendar_id.duration - int(calendar_id.duration)
            stop_date = next_date + timedelta(hours=duration)
            next_date = self.get_timezone_date(next_date)
            stop_date = self.get_timezone_date(stop_date)
            calendar_id.stop = stop_date
            calendar_id.start = next_date
            self.order_date = next_date
            self.expire_date = next_date.date() + timedelta(days=90)
            if prev_calendar_ids:
                prev_calendar_ids.unlink()
                self.last_update = 0
                self.calendar_updating()
        if 'delivery_lead_time' in vals.keys():
            if vals['delivery_lead_time'] > 365:
                raise UserError(_("This lead time is not valid, it should be under 365"))
        res = super(PurchaseSchedule, self).write(vals)

        return res

    @api.multi
    def unlink(self):
        """
        Function super for deleting purchase
        calendar record.
        """
        for recd in self:
            calendar_id = self.env['calendar.event'].search([('schedule_id', '=', recd.id)])
            calendar_id.unlink()
        return super(PurchaseSchedule, self).unlink()

    def calendar_updating(self):
        """
        created for cron job for checking
        expiration of records and create the
        calendar events as per the number of weeks
        in purchase configuration
        """
        number_of_weeks = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.number_of_weeks',
                                                                           default=False)
        if number_of_weeks:
            number_of_weeks = int(number_of_weeks)
            schedule_ids = self.search([])
            schedule_ids = schedule_ids.filtered(lambda s: s.last_update < number_of_weeks)
            for recd in schedule_ids:
                no_update = number_of_weeks - recd.last_update
                upd_date = recd.order_date.date()
                for i in range(no_update):
                    next_date = upd_date + timedelta(days=7)
                    upd_date = next_date
                    calendar_id = recd.partner_id.factory_calendar_id
                    use_time = self.get_worktime(calendar_id, recd.time) if calendar_id else recd.time
                    float_value = use_time - int(use_time)
                    flag_day = True
                    while flag_day:
                        if recd.partner_id.factory_calendar_id:
                            status = self.get_working_day(calendar_id.id, next_date)
                            if status != 0:
                                next_date = next_date + timedelta(days=status)
                            else:
                                flag_day = False
                        else:
                            flag_day = False
                    order_date = datetime(next_date.year, next_date.month, next_date.day, int(use_time), 0)

                    order_date = order_date + timedelta(hours=float_value)
                    duration = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.schedule_duration',
                                                                                default=False)
                    tags = self.env['ir.config_parameter'].sudo().get_param('purchase_schedule.tags', default=False)
                    stop_date = order_date + timedelta(minutes=int(duration))
                    order_date = self.get_timezone_date(order_date)
                    stop_date = self.get_timezone_date(stop_date)
                    buyer_ids = recd.partner_id.buyer_id.partner_id.ids if recd.partner_id.buyer_id else []
                    vals = {
                        'name': "Order " + recd.partner_id.name,
                        'start': order_date,
                        'stop': stop_date,
                        'categ_ids': [(6, 0, ast.literal_eval(str(tags)))] if tags else False,
                        'schedule_id': recd.id,
                        'partner_ids': [(6, 0, ast.literal_eval(str(buyer_ids)))]
                    }

                    calendar_obj = self.env['calendar.event']
                    calendar_obj.create(vals)
                recd.last_update = number_of_weeks
        schedule_ids = self.search([('expire_date', '<=', date.today())])

        schedule_ids.unlink()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    schedule_ids = fields.One2many('purchase.schedule',
                                   'partner_id', 'Schedule Info')
    buyer_id = fields.Many2one('res.users', "Buyer")


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    schedule_id = fields.Many2one('purchase.schedule', string="Purchase Schedule", readonly=True)
