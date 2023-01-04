from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    started_job = fields.Boolean(default=False)
    async_state = fields.Selection(
        selection=[
            ('progress', 'Confirm in progress'),
            ('done', 'Done'),
        ],
        default=False
    )

    def action_async_confirm(self):
        for rec in self:
            rec.async_state = 'progress'
            rec.with_delay(max_retries=4, eta=2).confirm_purchase_order()
        return True

    @job(default_channel='root.purchase_order')
    @api.multi
    def confirm_purchase_order(self):
        if self.started_job is True:
            raise Exception(_('Job already started, prevented rerun'))
        self.write({'started_job': True})
        self.env.cr.commit()
        context = dict(self.env.context)
        context.update({'ignore_reservation': True})
        res = self.with_context(context).button_confirm()
        for rec in self:
            rec.async_state = 'done'
        return res
