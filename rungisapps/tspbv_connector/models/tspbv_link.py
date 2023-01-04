from odoo import api, fields, models


class Link(models.Model):
    _name = 'tspbv.link'
    _description = 'Lydia Link'

    rel = fields.Char(string='Relation ID')
    dialog_id = fields.Many2one(
        comodel_name='tspbv.dialog',
        string='Dialog'
    )
    href = fields.Char(string='Redirect URL (href)')
    method = fields.Selection(
        string='Method',
        selection=[('post', 'POST'), ('get', 'GET'), ('put', 'PUT')]
    )
    sub_dialog_id = fields.Many2one(
        comodel_name='tspbv.dialog',
        string='Sub Dialog'
    )

    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.rel

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res
