from odoo import models, fields, api


class StockGate(models.Model):
    _name = 'stock.gate'
    _description = 'Stock Gate'
    _sql_constraints = [
         ('name_unique', 'unique (name)', 'This gate already exists!')]

    name = fields.Char()

    state = fields.Boolean(
        default=False,
        string="Occupied",
        help="Indicated if a Gate has a Picking assigned or not"
    )
    
    active = fields.Boolean(
        default=True,
        string="Active",
        help="Gate is available or maybe down for maintance etc."
    )
