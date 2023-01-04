from contextlib import contextmanager
from odoo import api, fields, models
from datetime import datetime, timedelta
from ..components.backend_adapter import DB2Connect
from odoo.exceptions import AccessError
import pytz

IMPORT_DELTA_BUFFER = 30  # second


class Db2Backend(models.Model):
    _name = 'db2.backend'
    _inherit = 'connector.backend'
    _description = 'DB2 Backend'

    name = fields.Char(required=True)
    database = fields.Char(required=True)
    hostname = fields.Char(required=True)
    port = fields.Integer(required=True)
    uid = fields.Char()
    pwd = fields.Char()
    split_companies = fields.Boolean(default=False)
    default_company_id = fields.Many2one(comodel_name='res.company')
    default_warehouse_id = fields.Many2one(comodel_name='stock.warehouse')
    active = fields.Boolean(default=True)
    sale_order_table = fields.Char()
    is_time_restricted = fields.Boolean(string='restrict time')
    between_start = fields.Float(string='start (hour)')
    between_end = fields.Float(string='end (hour)')
    sale_order_filter = fields.One2many(comodel_name='db2.filter.line', inverse_name='backend_id')

    def convert_time_to_float(self, datetime_stamp):
        return float(datetime_stamp.hour + (datetime_stamp.minute / 60))

    @api.multi
    def import_sale_orders(self):
        import_start_time = datetime.now()

        time_zone = pytz.timezone(
            self.env.user.tz or 'UTC'
        )
        import_start_time = pytz.utc.localize(
            import_start_time,
            is_dst=None).astimezone(time_zone)
        if (
            self.is_time_restricted is True and
            (
                self.between_start >= self.convert_time_to_float(import_start_time) or
                self.between_end <= self.convert_time_to_float(import_start_time)
            )
        ):
            return True

        sale_binding_model = self.env['db2.sale.order']
        sale_binding_model = sale_binding_model.sudo()

        backend = self
        # first job starts here
        delayable = sale_binding_model.with_delay(priority=1)
        filters = {
            'from_date': '2021-01-01',
            'to_date': '2021-10-01',
        }
        if len(self.sale_order_filter):
            if 'where' not in filters:
                filters.update({
                    'where': []
                })
            for sof in self.sale_order_filter:
                filters['where'] += [[sof.attributes, sof.condition, sof.value]]

        delayable.import_batch(backend, filters=filters)
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_orders_from_date': next_time})
        return True

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        with DB2Connect(self.database, self.hostname, self.port, self.uid, self.pwd) as db2_api:
            _super = super(Db2Backend, self)
            # from the components we'll be able to do: self.work.magento_api
            with _super.work_on(
                    model_name, db2_api=db2_api, **kwargs) as work:
                yield work

    def test_connection(self):
        try:
            db2_api = DB2Connect(self.database, self.hostname, self.port, self.uid, self.pwd)
            select_string = ("select * from %(sale_order_table)s where OAUSTAT != '1' AND OAUSTAT != '9'") % {'sale_order_table': self.sale_order_table}
            res = db2_api.api_call(select_string, 'read')
            if (len(res) > 0):
                return True
        except Exception as e:
            raise AccessError(e)
