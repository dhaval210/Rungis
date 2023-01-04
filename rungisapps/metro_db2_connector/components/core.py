from odoo.addons.component.core import AbstractComponent


class BaseMagentoConnectorComponent(AbstractComponent):
    """ Base DB2 Connector Component
    All components of this connector should inherit from it.
    """

    _name = 'base.db2.connector'
    _inherit = 'base.connector'
    _collection = 'db2.backend'
