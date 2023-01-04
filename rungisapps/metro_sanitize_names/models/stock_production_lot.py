from odoo import models, api
import string


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def create(self, vals):
        if 'name' in vals:
            filtered_string = ''.join([x for x in vals['name'] if x in string.printable])
            vals.update({'name': filtered_string})
        return super().create(vals)

    @api.multi
    def write(self, values):
        if 'name' in values:
            filtered_string = ''.join([x for x in values['name'] if x in string.printable])
            values.update({'name': filtered_string})
        return super().write(values)
