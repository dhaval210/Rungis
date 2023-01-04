from odoo.addons.component.core import AbstractComponent
import logging
_logger = logging.getLogger(__name__)


class CSVExportMapper(AbstractComponent):
    _name = 'csv.export.mapper'
    _inherit = ['base.csv.connector', 'base.export.mapper']
    _usage = 'export.mapper'
