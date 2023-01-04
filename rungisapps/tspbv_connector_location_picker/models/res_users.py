from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _read_group_picker_location_ids(self, stages, domain, order):
        return self.env["tspbv.picker"].search([])

    picker_location_id = fields.Many2one(
        comodel_name='tspbv.picker',
        string='Picking Location',
        group_expand='_read_group_picker_location_ids',
    )
