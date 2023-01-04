from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    softm_location_number = fields.Integer(
        'SoftM Lagernummer',
        related="product_variant_ids.softm_location_number"
    )
    net_weight = fields.Float(string='Net weight')
    abc_class1 = fields.Char()
    abc_class3 = fields.Char()
    scientific_name = fields.Char()
    categ2_ids = fields.Many2many(
        comodel_name='product.category', relation='product_categ2_rel',
        column1='product_id', column2='categ_id', string='Extra categories2')


    @api.multi
    def _compute_valid_attributes(self):
        """A product template attribute line is considered valid if it has at
        least one possible value.

        Those with only one value are considered valid, even though they should
        not appear on the configurator itself (unless they have an is_custom
        value to input), indeed single value attributes can be used to filter
        products among others based on that attribute/value.

        A product attribute value is considered valid for a template if it is
        defined on a product template attribute line.

        A product attribute is considered valid for a template if it
        has at least one possible value set on the template.

        For what is considered an archived variant, see `_has_valid_attributes`.
        """
        # prefetch
        self.mapped('attribute_line_ids.value_ids.id')
        self.mapped('attribute_line_ids.attribute_id.create_variant')

        for record in self:
            record.valid_product_template_attribute_line_ids = record.attribute_line_ids.filtered(lambda ptal: ptal.value_ids)
            record.valid_product_template_attribute_line_wnva_ids = record.valid_product_template_attribute_line_ids._without_no_variant_attributes()

            record.valid_product_attribute_value_ids = record.valid_product_template_attribute_line_ids.mapped('value_ids')
            error = {}
            for value in record.valid_product_attribute_value_ids:
                if 'fishing area' in value.attribute_id.name.lower() and value.softm_key is False:
                    if value.attribute_id.name not in error:
                        error.update({
                            value.attribute_id.name: [value.name]
                        })
                    else:
                        error[value.attribute_id.name] += [value.name]
            if len(error):
                e_string = ''
                for attr, values in error.items():
                    e_string += '''
                        attribute: %s
                        value(s): \n %s                    
                    ''' % (attr, '\n'.join(values))
                e_string += '\n missing softm_key'
                raise ValidationError(
                    e_string
                )                
            record.valid_product_attribute_value_wnva_ids = record.valid_product_template_attribute_line_wnva_ids.mapped('value_ids')

            record.valid_product_attribute_ids = record.valid_product_template_attribute_line_ids.mapped('attribute_id')
            record.valid_product_attribute_wnva_ids = record.valid_product_template_attribute_line_wnva_ids.mapped('attribute_id')
