from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class DB2Binding(models.AbstractModel):
    """ Abstract Model for the Bindings.
    """
    _name = 'db2.binding'
    _inherit = 'external.binding'
    _description = 'DB2 Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='db2.backend',
        string='DB2 Backend',
        required=True,
        ondelete='restrict',
    )
    external_id = fields.Char(string='ID in DB2')

    _sql_constraints = [
        (
            'db2_uniq', 'unique(backend_id, external_id)',
            'A binding already exists with the same DB2 ID.'
        ),
    ]

    @job(default_channel='root.db2')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on DB2 """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.db2')
    @related_action(action='related_action_db2_link')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a DB2 record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.batch_run(external_id, force=force)

    @job(default_channel='root.db2')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def export_record(self, fields=None):
        """ Export a record on DB2 """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.db2')
    @related_action(action='related_action_db2_link')
    def export_delete_record(self, backend, external_id):
        """ Delete a record on DB2 """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(external_id)
