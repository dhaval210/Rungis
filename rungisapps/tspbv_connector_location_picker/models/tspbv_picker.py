from odoo import api, fields, models


class TspbvPicker(models.Model):
    _name = 'tspbv.picker'
    _description = 'Picker Assignment'
    _rec_name = 'location_id'
    _desc_name = 'location_id'

    location_id = fields.Many2one(comodel_name='stock.location')
    active = fields.Boolean()
