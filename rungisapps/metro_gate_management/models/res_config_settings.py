from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Gate Management Settings'

    operation_type = fields.Selection([('Receipts', 'Receipts'), ('Internal Transfers', 'Internal Transfers'), ('Delivery Orders', 'Delivery Orders')], default='Receipts')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        operation_type = params.get_param('operation_type', default='Receipts')
        res.update(
            operation_type=operation_type
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('operation_type',
                                                         self.operation_type)
