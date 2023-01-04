# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from datetime import timedelta, datetime, date
import pytz
import logging

from odoo.exceptions import UserError

class TourAssignment(models.Model):
    _name = "tour.assignment"
    _description = "Tour assignment"

    partner_id = fields.Many2one('res.partner', 'Partner', index=True, ondelete='cascade')
    #related partner fields
    ref = fields.Char('Kundennummer', related='partner_id.ref')
    zip = fields.Char('PLZ', related='partner_id.zip')

    order_deadline = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Order day of week', required=True, index=True, default='0')

    tour_id = fields.Many2one('transporter.route', string="Tour")
    #related tour fields
    tour_default_departure = fields.Float('Default Departure', related='tour_id.tour_default_departure')
    tour_depot = fields.Char('Tour Depot', related='tour_id.tour_depot', store=True)
    tour_group = fields.Char('Tour Group', related='tour_id.tour_group', store=True)

    hub_id = fields.Many2one('transporter.hub', string="Hub")
    # related hub fields
    default_arrival_float = fields.Float('Planned Arrival', related='hub_id.default_arrival_float')
    default_departure_float = fields.Float('Planned Departure', related='hub_id.default_departure_float')

    drop_off = fields.Integer('Drop Off Nr.')

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

    def action_generate_so(self):
        return self.cron_generate_so(cron_mode=False)

    def cron_generate_so(self,cron_mode=True):
        logger = logging.getLogger(__name__)
        logger.info(
            'Start tour assignment SO generation with '
            'user %s ID %d', self.env.user.name, self.env.user.id)
        if cron_mode:
            records = self.search([])
        else:
            records = self
        for i in records:
            next_date = date.today() + timedelta(
                (int(i.order_deadline) - date.today().weekday()) % 7)
            calling_hour = int(i.partner_id.calling_time)
            calling_minute = int(i.partner_id.calling_time % 1 * 60)
            order_date = datetime(next_date.year, next_date.month, next_date.day, calling_hour, calling_minute)
            order_date = self.get_timezone_date(order_date)
            existing_so = self.env['sale.order'].search([
                ('partner_id','=',i.partner_id.id),
                ('date_order','>=',order_date.date()),
                ('date_order','<',order_date.date()+timedelta(days=1)),
            ])

            #commented as testing data all "lost customer"
            #if not existing_so and not i.partner_id.lost_customer:

            if not existing_so:
                user_id = i.partner_id.user_id.id
                emp_id = i.partner_id.user_id.employee_ids
                if emp_id:
                    emp_leave_id = self.env['hr.leave'].search([
                        ('employee_id', '=', emp_id[0].id),
                        ('date_from', '<=', order_date),
                        ('date_to', '>=', order_date),
                        ('state', '=', 'validate')
                    ])
                    if emp_leave_id:
                        substitute_emp_id = i.partner_id.substitute_user_id.employee_ids
                        if substitute_emp_id:
                            substitute_emp_leave_id = self.env['hr.leave'].search([
                                ('employee_id', '=', substitute_emp_id[0].id),
                                ('date_from', '<=', order_date),
                                ('date_to', '>=', order_date),
                                ('state', '=', 'validate')
                            ])
                            if substitute_emp_leave_id:
                                user_id = False
                            else:
                                user_id = i.partner_id.substitute_user_id.id


                new_so = self.env['sale.order'].create({
                    'partner_id': i.partner_id.id,
                    'tour_id': i.tour_id.id,
                    'sequence': i.drop_off,
                    'date_order': order_date,
                    'calling_date': order_date,
                    'commitment_date': order_date,
                    'user_id': user_id,
                })
                logger.info("Created %s" %(new_so.name))
        logger.info('End of tour assignment SO generation')


class TransporterRoute(models.Model):
    _inherit = 'transporter.route'

    capacity = fields.Float("Capacity (kg)", help="The capacity in kg of the route")