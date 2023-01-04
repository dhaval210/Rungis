# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo import api, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def _assign_picking(self):
        res = super(StockMove, self)._assign_picking()
        for record in self:
            if record.picking_id:
                record.picking_id.write({'picking_treated': False})
        return res
