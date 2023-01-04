from odoo import models, fields, api


class KsPivotStatus(models.TransientModel):
    # Inherited res.config.settings to display the pivot on the general setting.
    _inherit = 'res.config.settings'
    ks_pivot_status_header = fields.Boolean(config_parameter='base_setup.ks_pivot_sticky_status')


class KsHttp(models.AbstractModel):
    _inherit = 'ir.http'

    # Set pivot status to the session.
    def session_info(self):
        rec = super(KsHttp, self).session_info()
        rec['ks_pivot_status_header'] = self.env['ir.config_parameter'].sudo().get_param('base_setup'
                                                                                         '.ks_pivot_sticky_status')
        return rec
