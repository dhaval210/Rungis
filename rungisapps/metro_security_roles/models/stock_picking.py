from odoo import api, fields, models, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        context = self.env.context.copy()
        context['allow_picking_reservation'] = True
        self.env.context = context
        return super().button_validate()
