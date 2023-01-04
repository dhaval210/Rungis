from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job
from odoo.exceptions import ValidationError, UserError
from odoo.addons.queue_job.exception import RetryableJobError
from psycopg2.extensions import TransactionRollbackError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    started_job = fields.Boolean(default=False)

    def async_confirm(self):
        self.with_delay(max_retries=4, eta=2).confirm_sale_order()
        return True

    @job(default_channel='root.sale_order',)
    @api.model
    def confirm_sale_order(self):
        if self.started_job is True:
            raise Exception(_('Job already started, prevented rerun'))
        self.write({'started_job': True})
        self.env.cr.commit()
        try:
            context = dict(self.env.context)
            context.update({'ignore_reservation': True})
            self.with_context(context).action_confirm()
        except TransactionRollbackError as e:
            sol_count = len(self.order_line)
            raise RetryableJobError(
                e,
                seconds=((5 * 60) + sol_count),
                ignore_retry=False
            )
        return True
