# -*- coding: utf-8 -*-

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def button_confirm(self):
        super(PurchaseOrder, self).button_confirm()
        if self.user_id.id == 1:
            self.user_id = self.env.uid