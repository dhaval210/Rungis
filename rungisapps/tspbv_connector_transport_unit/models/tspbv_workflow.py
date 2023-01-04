from odoo import fields, models


class TspbvWorkflow(models.Model):
    _inherit = 'tspbv.workflow'

    transport_unit_dialoglist = fields.Many2one(comodel_name='tspbv.dialoglist')
    stash_dialoglist = fields.Many2one(comodel_name='tspbv.dialoglist')
