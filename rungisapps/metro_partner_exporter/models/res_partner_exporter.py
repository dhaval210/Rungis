from odoo.addons.component.core import Component
import logging
_logger = logging.getLogger(__name__)


class ResPartnerExporter(Component):
    _name = 'res.partner.exporter'
    _inherit = 'csv.exporter'
    _apply_on = ['res.partner']
    _usage = 'record.exporter'
