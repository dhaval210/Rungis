from odoo import models, api, fields


class MyModuleMessageWizard(models.TransientModel):
    _name = 'message.wiz'
    _description = "Show Message"

    message = fields.Text('Message', required=True)

    @api.multi
    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
