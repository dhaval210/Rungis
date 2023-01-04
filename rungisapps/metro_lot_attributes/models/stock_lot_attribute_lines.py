import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LotAttributeLines(models.Model):
    _name = 'stock.lot.attribute.lines'
    _description = 'Lot Attribute Lines'

    active = fields.Boolean(default=True)
    lot_id = fields.Many2one(
        'stock.production.lot',
        ondelete='restrict',
        index=True
    )
    line_id = fields.Many2one(
        'stock.move.line',
        ondelete='restrict',
        index=True
    )

    product_tmpl_id = fields.Many2one(
        'product.template',
    )

    attribute_line_id = fields.Many2one(
        comodel_name='product.template.attribute.line',
        readonly=True,
    )

    valid_product_attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        related='product_tmpl_id.valid_product_attribute_value_ids',
        readonly=True,
        auto_join=True,
    )

    attribute_id = fields.Many2one(
        'product.attribute',
        string="Attribute",
        ondelete='restrict',
        required=True,
        index=True
    )

    mandatory = fields.Boolean()

    value_ids = fields.Many2one(
        'product.attribute.value',
        string="Values",
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        attribute_ids = res.valid_product_attribute_value_ids.mapped('attribute_id').ids
        if 'attribute_id' in vals and vals.get('attribute_id') not in attribute_ids:
            raise ValidationError('attribute is not allowed. set lot_extension at attribute line to use it in lot')
        return res
