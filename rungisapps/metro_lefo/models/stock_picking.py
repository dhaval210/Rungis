from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        context = self.env.context.copy()
        context.update({'partner': self.partner_id.id})
        self.env.context = context
        return super().action_done()
