from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id',
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')], compute="get_default_tax", readonly=False)

    def get_default_tax(self):
        for record in self:
            if self.env['res.company']._company_default_get().id == 4:
                taxes = self.env['account.tax'].search([('name', '=', 'M3 Umsatzsteuer WVK LJ 10%')]).ids
                record.taxes_id = False
                record.taxes_id = [(6, 0, taxes)]
            else:
                taxes = self.env.user.company_id.account_sale_tax_id.ids
                record.taxes_id = False
                record.taxes_id = [(6, 0, taxes)]


