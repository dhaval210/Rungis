from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class BatchPicling(models.Model):
    _inherit = 'stock.picking.batch'

    voice_picked = fields.Boolean(string='picked by voice')
    use_voice_pick = fields.Boolean(string='use for pbv')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Running'),
        ('done', 'Done'),
        ('on_hold', 'On Hold'),
        ('cancel', 'Cancelled')],
        default='draft',
        copy=False,
        track_visibility='onchange',
        required=True
    )

    progress = fields.Float(compute="_compute_progress", store=True)

    @api.multi
    def unhold(self):
        self.ensure_one()
        self.state = 'in_progress'
        return self

    @api.depends('picking_ids.move_line_ids.voice_picked')
    def _compute_progress(self):
        for batch in self.filtered(lambda x: x.state not in ['done', 'cancel']):
            complete_count = len(batch.picking_ids.mapped('move_line_ids'))
            picked_count = len(batch.picking_ids.mapped('move_line_ids').filtered(
                lambda x: x.voice_picked == True
            ))
            if complete_count > 0:
                batch.progress = float_round(picked_count / complete_count * 100, precision_rounding=0.01)
