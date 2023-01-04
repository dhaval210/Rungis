from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    voice_picked = fields.Boolean(string='picked by voice')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('on_hold', 'On hold'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    session_id = fields.Many2one(
        comodel_name='tspbv.session',
        string='PbV Session ID'
    )

    @api.multi
    def unhold(self):
        self.ensure_one()
        self.state = 'assigned'
        return self
