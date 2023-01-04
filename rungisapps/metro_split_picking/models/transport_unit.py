from odoo import _, api, fields, models, tools
from odoo.addons import decimal_precision as dp


class TransportUnit(models.Model):
    _name = 'transport.unit'

    name = fields.Char(string='Name', required=True)
    max_weight_capacity = fields.Float('Weight Capacity(kg)')
    max_volume_capacity = fields.Float(
        'Volume Capacity(m³)',
        digits=dp.get_precision('Volume Capacity')
    )
