from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    used_for_aproduct = fields.Boolean('Used for simplified Aproduct Auto workflow', default=False)
    aproduct_exclude_location_ids = fields.Many2many('stock.location', 'stock_warehouse_aproduct_excluded_location_rel')
