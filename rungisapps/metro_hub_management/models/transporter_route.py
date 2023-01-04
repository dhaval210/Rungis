from odoo import api, fields, models


class Route(models.Model):
    _inherit = 'transporter.route'

    hub_id = fields.Many2one(
        comodel_name='transporter.hub',
        group_expand='_read_group_hub_ids'
    )

    # Show Hubs in Kanban View even if empty
    @api.model
    def _read_group_hub_ids(self, stages, domain, order):
        hub_ids = self.env['transporter.hub'].search([])
        return hub_ids
