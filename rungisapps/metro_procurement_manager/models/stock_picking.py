from odoo import api, fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def force_action_assign(self):
        context = dict(self.env.context)
        context.update({'force_reservation': True})
        return self.with_context(context).action_assign()
