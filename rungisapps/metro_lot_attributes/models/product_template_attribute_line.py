from odoo import api, fields, models


class TemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    print_on_invoice = fields.Boolean()
    lot_extension = fields.Boolean()
    mandatory = fields.Boolean()
    product_label_info = fields.Boolean()
