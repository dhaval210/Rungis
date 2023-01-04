from odoo import api, fields, models


class Dialog(models.Model):
    _name = 'tspbv.dialog'
    _description = 'Dialog'

    id_dialog = fields.Char(string='ID')
    dialoglist_id = fields.Many2one(comodel_name='tspbv.dialoglist', string='Dialoglist')
    lydia_output_id = fields.Many2one(comodel_name='tspbv.output', string='Lydia Output')
    lydia_input_id = fields.Many2one(comodel_name='tspbv.input', string='Lydia Input')
    lydia_link_ids = fields.One2many(comodel_name='tspbv.link', inverse_name='dialog_id', string='Links')
    terminate = fields.Boolean(string='Terminate Session', default=False)

    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.id_dialog

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res
