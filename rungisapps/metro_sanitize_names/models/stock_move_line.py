from odoo import models, api
import string


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def create(self, vals):
        if 'lot_name' in vals:
            filtered_string = ''.join([x for x in vals['lot_name'] if x in string.printable])
            vals.update({'lot_name': filtered_string})
        return super().create(vals)

    @api.multi
    def write(self, values):
        if 'lot_name' in values:
            filtered_string = ''.join([x for x in values['lot_name'] if x in string.printable])
            values.update({'lot_name': filtered_string})
        return super().write(values)
