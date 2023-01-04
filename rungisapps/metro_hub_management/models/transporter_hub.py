from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
import pytz


class Hub(models.Model):
    _name = 'transporter.hub'
    _description = 'Hub'
    _order = 'departure_time'

    NEW_DAY_HOUR = '06:00:00'

    name = fields.Char(required=True)
    arrival_time = fields.Datetime(string='Arrival Today',)
    departure_time = fields.Datetime(string='Departure Today',)
    default_arrival_time = fields.Datetime(compute='_compute_default_arrival_time', store=True)
    default_arrival_float = fields.Float()
    default_departure_time = fields.Datetime(compute='_compute_default_departure_time', store=True)
    default_departure_float = fields.Float()
    tour_ids = fields.One2many(comodel_name='transporter.route', inverse_name='hub_id')
    schedule_ids = fields.One2many(comodel_name='transporter.hub.schedule', inverse_name='hub_id')
    active = fields.Boolean(default=True)

    @api.depends('default_departure_float')
    def _compute_default_departure_time(self):
        for rec in self:
            rec.default_departure_time = self.get_time_from_float(rec.default_departure_float, fields.Datetime().now())

    @api.depends('default_arrival_float')
    def _compute_default_arrival_time(self):
        for rec in self:
            rec.default_arrival_time = self.get_time_from_float(rec.default_arrival_float, fields.Datetime().now())

    def get_time_from_float(self, float_time, date_time):
        val = date_time
        if float_time < 6:
            val = val + relativedelta(days=1)
        minutes = float_time * 60
        minutes = relativedelta(minutes=minutes)            
        val = val.replace(hour=0, minute=0, second=0)
        val = val + minutes
        tz = pytz.timezone(self.env.user.tz or 'UTC')      
        offset = tz.utcoffset(val)        
        return val - offset

    @api.multi
    def name_get(self):
        result = []
        for r in self:
            if r.departure_time is not False:
                time_zone = pytz.timezone(
                    self.env.user.tz or 'UTC'
                )
                current_time = pytz.utc.localize(
                    r.departure_time,
                    is_dst=None).astimezone(time_zone)
                formatted_current_time = current_time.strftime('%H:%M')
                time = formatted_current_time
            else:
                time = '-'
            result.append((r.id, '%s (%s)' % (r.name, time)))
        return result

    def set_departure_times(self):
        yesterday = (fields.Datetime().now() - relativedelta(days=1)).strftime('%Y-%m-%d ' + self.NEW_DAY_HOUR)
        today = fields.Datetime().now().strftime('%Y-%m-%d ' + self.NEW_DAY_HOUR)
        tomorrow = (fields.Datetime().now() + relativedelta(days=1)).strftime('%Y-%m-%d ' + self.NEW_DAY_HOUR)
        hubs = self.search([])
        for hub in hubs:
            schedule = hub.schedule_ids.filtered(
                lambda x: 
                    x.departure_day.strftime('%Y-%m-%d H:M:S') > yesterday and
                    x.departure_day.strftime('%Y-%m-%d H:M:S') < today and
                    (x.active == True or x.active == False)
            )

            btchs = self.env['stock.picking.batch'].search(
                [
                    ('hub_id', '=', hub.id),
                    ('create_date', '>', yesterday),
                    ('create_date', '<', today),
                ],
                order="write_date DESC",
            )  
            data = {
                'active': False,
            }                      
            if len(btchs) > 0:
                newest = self.env['stock.picking'].search(
                    [
                        ('batch_id', 'in', btchs.ids),
                        ('state', '=', 'done'),
                        ('create_date', '>', yesterday),
                        ('create_date', '<', today),
                    ],
                    order="write_date DESC",
                    limit=1
                )
                oldest = self.env['stock.picking.batch'].search(
                    [
                        ('hub_id', '=', hub.id),
                        ('state', '=', 'done'),
                        ('create_date', '>', yesterday),
                        ('create_date', '<', today),
                    ],
                    order="create_date ASC",
                    limit=1
                )
                data.update({
                    'picking_start_date': oldest.create_date,
                    'picking_end_date': newest.write_date,
                })
            if len(schedule):
                schedule.write(data)
            schdls = self.env['transporter.hub.schedule'].search(
                [
                    ('hub_id', '=', hub.id),
                    ('departure_day', '>', today),
                    ('departure_day', '<', tomorrow)
                ]
            )
            if len(schdls) > 0:
                hub.departure_time = schdls.departure_day
                hub.arrival_time = schdls.planned_arrival_date
            else:
                if hub.default_departure_time and hub.default_departure_time.hour > 5:
                    departure = fields.Datetime().now()
                else:
                    departure = (fields.Datetime().now() + relativedelta(days=1))
                if hub.default_arrival_time and hub.default_arrival_time.hour > 5:
                    arrival = fields.Datetime().now()
                else:
                    arrival = (fields.Datetime().now() + relativedelta(days=1))
                departure = departure.replace(
                    hour=hub.default_departure_time.hour,
                    minute=hub.default_departure_time.minute,
                    second=0
                )
                arrival = arrival.replace(
                    hour=hub.default_arrival_time.hour,
                    minute=hub.default_arrival_time.minute,
                    second=0
                )
                hub.departure_time = departure
                hub.arrival_time = arrival
        return True


class HubSchedule(models.Model):
    _name = 'transporter.hub.schedule'
    _description = 'Hub Schedule'
    _rec_name = 'departure_day'
    _order = 'departure_day'

    planned_arrival_date = fields.Datetime(string="Planned Arrival", required=True)
    real_arrival_date = fields.Datetime(string="Real Arrival")
    departure_day = fields.Datetime(string="Planned Departure", required=True)
    picking_start_date = fields.Datetime(string="Picking Start")
    picking_end_date = fields.Datetime(string="Picking End")
    real_departure_day = fields.Datetime(string="Real Departure")
    hub_id = fields.Many2one(comodel_name='transporter.hub')
    active = fields.Boolean(default=True)

    @api.multi
    def name_get(self):
        result = []
        for r in self:
            tz = self.env.user.tz
            time_zone = pytz.timezone(
                self.env.user.tz or 'UTC'
            )
            current_time = pytz.utc.localize(
                r.departure_day,
                is_dst=None).astimezone(time_zone)
            formatted_current_time = current_time.strftime('%d.%m.%Y')
            day = formatted_current_time
            time = current_time.strftime('%H:%M')
            result.append((r.id, '%s %s' % (day, time)))
        return result
