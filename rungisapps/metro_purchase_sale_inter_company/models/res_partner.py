from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    company_ids = fields.Many2many('res.company', 'res_partner_company_access_rel', 'partner_id', 'company_id')


class Product(models.Model):
    _inherit = 'product.template'

    company_ids = fields.Many2many('res.company', 'product_template_company_access_rel', 'product_template_id', 'company_id')
