from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    volume = fields.Float(
        'Volume',
        compute='_compute_volume',
        inverse='_set_volume',
        help="The volume in m3.",
        digits=dp.get_precision('Product Volume'),
        store=True
    )
