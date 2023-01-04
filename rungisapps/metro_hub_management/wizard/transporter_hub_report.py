from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import models, fields
import pytz


class LotBarcodeLine(models.TransientModel):
    _name = "transporter.hub.line"
    _description = 'Hub Schedule Line'

    hub_id = fields.Many2one(comodel_name='transporter.hub')
    planned_arrival = fields.Datetime()
    planned_arrival_float = fields.Float()
    planned_departure = fields.Datetime()
    planned_departure_float = fields.Float()
    wizard_id = fields.Many2one('transporter.hub.report', string="Wizard")


class HubReport(models.TransientModel):
    _name = "transporter.hub.report"
    _description = 'Hub Report'

    def _default_hub_lines(self):
        result = []
        active_ids = self.env.context.get('active_ids', [])
        hub_ids = self.env['transporter.hub'].search([('id', 'in', active_ids)])
        for hub_id in hub_ids:
            arrival_time = hub_id.default_arrival_time
            departure_time = hub_id.default_departure_time
            tz = pytz.timezone(self.env.user.tz or 'UTC')      
            offset = tz.utcoffset(arrival_time)
            arrival_time += offset
            departure_time += offset
        
            arrival_float = (arrival_time.hour * 60 + arrival_time.minute) / 60
            departure_float = (departure_time.hour * 60 + departure_time.minute) / 60
            result += [(
                0,
                0,
                {
                    'hub_id': hub_id,
                    'planned_arrival_float': arrival_float,
                    'planned_departure_float': departure_float,
                }
            )]
        return result

    schedule_date = fields.Date(default=fields.Date.today())
    hub_line_ids = fields.One2many('transporter.hub.line', 'wizard_id', default=_default_hub_lines)

    def generate_lines(self):
        schedule = self.env['transporter.hub.schedule']
        hub = self.env['transporter.hub']
        schedule_date = fields.Datetime().now()
        schedule_date = schedule_date.replace(
            day=self.schedule_date.day,
            month=self.schedule_date.month,
            year=self.schedule_date.year,
            hour=0,
            minute=0,
            second=0,
        )
        today = schedule_date.strftime('%Y-%m-%d ' + hub.NEW_DAY_HOUR)
        tomorrow = (schedule_date + relativedelta(days=1)).strftime('%Y-%m-%d ' + hub.NEW_DAY_HOUR)
        for line in self.hub_line_ids:
            new_line_arr_date = line.hub_id.get_time_from_float(line.planned_arrival_float, schedule_date)
            new_line_dep_date = line.hub_id.get_time_from_float(line.planned_departure_float, schedule_date)
            schdls = schedule.search(
                [
                    ('hub_id', '=', line.hub_id.id),
                    ('departure_day', '>', today),
                    ('departure_day', '<', tomorrow)
                ]
            )
            if len(schdls) > 0:
                raise ValidationError('Schedule for this Date already exists')
            else:
                if line.hub_id.id is not False:
                    schedule.create({
                        'active': True,
                        'hub_id': line.hub_id.id,
                        'departure_day': new_line_dep_date,
                        'planned_arrival_date': new_line_arr_date,
                    })
        return self.env['transporter.hub.schedule'].browse(self.hub_line_ids)