from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    removal_strategy_id = fields.Many2one('product.removal', 'Removal Strategy')