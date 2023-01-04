import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
from odoo.addons.connector.exception import IDMissingInBackend
from ..components.mapper import normalize_datetime

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    _name = 'db2.sale.order.batch.importer'
    _inherit = 'db2.delayed.batch.importer'
    _apply_on = 'db2.sale.order'

    def _import_record(self, external_id, job_options=None, **kwargs):
        job_options = {
            'max_retries': 0,
            'priority': 5,
        }
        return super(SaleOrderBatchImporter, self)._import_record(
            external_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        filters.update({'groupby': 'OAUAUFN'})
        filters.update({'attributes': 'OAUAUFN'})
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        external_ids = self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
        )
        _logger.info('search for db2 saleorders %s returned %s',
                     filters, external_ids)
        if external_ids is not None and len(external_ids):
            for external_id in external_ids:
                queue_jobs_running = self.env['queue.job'].search([
                    ('model_name', '=', 'db2.sale.order'),
                    ('method_name', '=', 'import_record'),
                    ('func_string', 'ilike', external_id['OAUAUFN']),
                    ('state', 'in', ['pending', 'enqueued', 'started']),
                ], limit=1)
                if len(queue_jobs_running) == 0:
                    self._import_record(external_id['OAUAUFN'])
