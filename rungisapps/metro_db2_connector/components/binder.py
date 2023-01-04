from odoo.addons.component.core import Component


class DB2ModelBinder(Component):
    _name = 'db2.binder'
    _inherit = ['base.binder', 'base.db2.connector']
    _apply_on = [
        'db2.sale.order',
        'db2.sale.order.line',
    ]
