from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class DB2Deleter(AbstractComponent):
    """ Base deleter for DB2 """
    _name = 'db2.exporter.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, external_id):
        """ Run the synchronization, delete the record on DB2
        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(external_id)
        return _('Record %s deleted in DB2') % (external_id,)
