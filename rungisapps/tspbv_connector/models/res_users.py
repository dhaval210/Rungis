from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_picker = fields.Boolean(default=False)
    picker_count = fields.Integer(default=1)
    workflow_id = fields.Many2one(comodel_name='tspbv.workflow')
