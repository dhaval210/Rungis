# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import Warning


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    block_proposal_override = fields.Boolean("Block Proposal Override")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def write(self, vals):
        super(StockPicking, self).write(vals)
        for res in self:
            product_location_id = res.move_line_ids_without_package.mapped(
                'location_dest_id')
            package_location_id = res.package_level_ids_details.mapped(
                'location_dest_id')
            if product_location_id:
                for loc in product_location_id:
                    if loc.putaway_strategy_id.empty_location and \
                            self.picking_type_id.block_proposal_override:
                        availability = loc.quant_ids
                        if availability:
                            raise Warning(_('Location %s is not empty') %
                                          loc.name)
            if package_location_id:
                for pac in package_location_id:
                    if pac.putaway_strategy_id.empty_location and \
                            self.picking_type_id.block_proposal_override:
                        availability = pac.quant_ids
                        if availability:
                            raise Warning(_('Location %s is not empty ') %
                                          pac.name)