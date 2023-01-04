# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpBomLine(models.AbstractModel):
    _inherit = 'mrp.bom.line'

    auto_lot_creation = fields.Boolean(string='Auto Lot Creation')


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.constrains('bom_line_ids')
    def _check_auto_lot_creation(self):
        """ max one line of each BOM shall have this checkbox(auto lot creation) set"""
        for bom in self:
            bom_lines = bom.bom_line_ids.filtered(lambda l: l.auto_lot_creation)
            if len(bom_lines) > 1:
                raise ValidationError(_('Only one BOM-line shall have Auto Lot Creation mark as checked.'))


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def open_produce_product(self):
        action = super(MrpProduction, self).open_produce_product()
        raw_move = self.move_raw_ids.filtered(lambda m: m.bom_line_id.auto_lot_creation and m.state not in ('done', 'cancel'))
        if raw_move:
            action['context'] = {'auto_lot': False}
        else:
            action['context'] = {'lot_auto': False}
        return action
