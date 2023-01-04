from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)
from odoo.addons.queue_job.job import job


class CSVBackend(models.Model):
    _name = 'csv.backend'
    _description = 'CSV Backend'
    _inherit = 'connector.backend'

    name = fields.Char(string='Name')
    export_to_disk = fields.Boolean(string='Export to Disk')
    path = fields.Char(string='File Path')
    export_count = fields.Integer(compute='compute_exports')
    last_export_date = fields.Datetime('Last export date', readonly=1)
    file_type = fields.Selection([('sap_partner_exporter', 'sap_partner_exporter')])

    def compute_exports(self):
        for record in self:
            record.export_count = self.env['csv.export'].search_count([('backend_id','=', self.id)])

    @api.model
    def export_partners_delay(self, file_type):
        """
        Import partner with delay : used to create job
        :return:
        """
        self.with_delay(priority=30).export_partner_records(file_type)
        return True


    @api.multi
    def export_partners_delay_button(self):
        """
        Import partner with delay : used to create job (Button)
        :return:
        """
        self.with_delay(priority=30).export_partner_records('sap_partner_exporter')
        return True

    @job(default_channel='root.csv')
    @api.model
    def export_partner_records(self, file_type):
        backend_ids = self.env['csv.backend'].search([('file_type', '=', file_type)], limit=1)
        for backend_id in backend_ids:
            context = self.env.context.copy()
            context['backend_id'] = backend_id.id
            self.env.context = context
            with backend_id.work_on(model_name='res.partner') as work:
                exporter = work.component(usage='record.exporter')
                records_exported = exporter.run()
                now = fields.Datetime.now()
                backend_id.last_export_date = now
                return '{} Partner records have been exported'.format(str(len(records_exported)))
