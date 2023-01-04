from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    write_date = fields.Datetime(string='Last Updated on', readonly=True, track_visibility='onchange')

    @api.multi
    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'attribute_value_ids', 'attribute_line_ids'],
                         load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                'attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            mydict = {
                'id': product.id,
                'name': name,
                'default_code': product.default_code,
            }
            result.append(_name_get(mydict))
        return result


class ProductTemplate(models.Model):
    _inherit = "product.template"

    group_check = fields.Boolean("Group Check", compute="check_group")
    write_date = fields.Datetime(string='Last Updated on', readonly=True, track_visibility='onchange')
    main_categ_id = fields.Many2one('product.category', string="Main Group")

    def check_group(self):
        user = self.env.user
        if user.has_group('metro_rungis_views.group_article'):
            self.group_check = True
        else:
            self.group_check = False

    fao_fishing_technique_id = fields.Many2one(
        comodel_name='product.fao.fishing.technique',
        string='FAO Fishing Tech.',
        ondelete='restrict',
    )


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    create_variant = fields.Selection([
        ('no_variant', 'Never'),
        ('always', 'Always'),
        ('dynamic', 'Only when the product is added to a sales order')],
        default='no_variant',
        string="Create Variants",
        help="Check this if you want to create multiple variants for this attribute.", required=True)
