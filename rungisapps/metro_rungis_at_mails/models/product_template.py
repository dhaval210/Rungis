from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _compute_base_url(self):
        for rec in self:
            url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rec.base_url = url

    base_url = fields.Text(string="Base URL", compute="_compute_base_url")

    def create(self, vals_list):
        res = super(ProductTemplate, self).create(vals_list)
        res._compute_base_url()
        template = self.env.ref('metro_rungis_at_mails.email_template_master_data_updation')
        if template:
            if res.sale_ok is True:
                template.send_mail(res.id, force_send=True, raise_exception=False, email_values=None)

        return res
