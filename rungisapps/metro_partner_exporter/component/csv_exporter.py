from odoo.addons.component.core import Component
import logging
_logger = logging.getLogger(__name__)
from odoo import _


class CSVExporter(Component):
    _name = 'csv.exporter'
    _inherit = ['base.exporter', 'base.csv.connector']
    _usage = 'record.exporter'

    def run(self):
        """ Flow of the synchronization, implemented in inherited classes"""
        backend_adapter = self.component(usage='backend.adapter')
        mapper = self.component(usage='export.mapper')
        partner_records = self.env['res.partner'].with_context(active_test=False).search([('sap_exported', '=', False)])
        if not partner_records:
            return _('Nothing to export.')
        record_list = []
        for partner in partner_records:
            record_list += [mapper.map_record(partner).values()]
        backend_adapter.create(record_list)
        partner_records.write({'sap_exported': True})
        return partner_records.ids