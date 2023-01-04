from odoo.addons.component.core import AbstractComponent
import logging
_logger = logging.getLogger(__name__)


class BaseCSVConnectorComponent(AbstractComponent):
    _name = 'base.csv.connector'
    _inherit = 'base.connector'
    _collection = 'csv.backend'
