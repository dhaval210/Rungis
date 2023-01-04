from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    aproduct_factor = fields.Float('Aproduct Factor')

    def get_aproduct_factor(self):
        if self.aproduct_factor:
            return self.aproduct_factor
        elif self.parent_id:
            return self.parent_id.get_aproduct_factor()
        else:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            aproduct_factor = get_param('metro_rungis_mrp_autoworkflow.aproduct_factor')
            return float(aproduct_factor)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aproduct_loss_account_id = fields.Many2one('account.account', config_parameter='metro_rungis_mrp_autoworkflow.aproduct_loss_account_id')
    aproduct_factor = fields.Float('Aproduct Factor', config_parameter='metro_rungis_mrp_autoworkflow.aproduct_factor')
