# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _cron_generate_exp_transfer(self):
        latest_date = fields.Date.today() + timedelta(days=1)
        last_date = fields.Date.today() - timedelta(days=1)
        # select expired quants from internal locations
        quant_ids = self.search([
            ('lot_id.use_date', '<=', latest_date),
            ('lot_id.use_date', '>', last_date),
            ('location_id.usage', '=', 'internal',)
        ], order='location_id')
        # delete the created operations still in draft from the previous run
        self.env['stock.picking'].search([
            ('state', '=', 'draft'),
            ('group_id', '=', self.env.ref('metro_expired_transfer.stock_quant_auto_transfer_procurement_group').id),
        ]).unlink()
        return self.generate_exp_transfer(cron_quants=quant_ids)

    @api.returns('account.invoice')
    def generate_exp_transfer(self, cron_quants=False):
        picking = {}
        quants_to_add = cron_quants or self
        grouped_quants = {}
        # group the quants per location and product, sum the quantity
        for quant in quants_to_add:
            grouped_quants.setdefault(quant.location_id, {})
            grouped_quants[quant.location_id].setdefault(quant.product_id, {'quantity': 0.00, 'cw_quantity': 0.00})
            grouped_quants[quant.location_id][quant.product_id]['quantity'] += quant.quantity
            grouped_quants[quant.location_id][quant.product_id]['cw_quantity'] += quant.cw_stock_quantity

        # create one picking per location, create stock moves from the grouped quants
        for location in grouped_quants:
            sm_lines = []
            warehouse = location.get_warehouse()
            if warehouse:
                expired_product_type_id = location.get_warehouse().expired_product_type_id
                if not expired_product_type_id and cron_quants:
                    raise UserError(
                        _('You have to set an Expiry Picking Type on the Warehouse %s') % location.get_warehouse().name)
                for p_line in grouped_quants[location]:
                    product_id = p_line
                    qty = grouped_quants[location][p_line]['quantity']
                    cw_qty = grouped_quants[location][p_line]['cw_quantity']
                    if qty > 0:
                        sm_lines.append({
                            'name': '%s Scrap' % (product_id[0].display_name),
                            'product_id': product_id[0].id,
                            'product_uom': product_id[0].uom_id.id,
                            'product_uom_qty': qty,
                            'product_cw_uom_qty': cw_qty,
                            'product_cw_uom': product_id[0].cw_uom_id.id if product_id[0].catch_weight_ok else False,
                            'origin': 'Expired products',
                            'group_id': self.env.ref(
                                'metro_expired_transfer.stock_quant_auto_transfer_procurement_group').id,
                            'location_id': location.id,
                            'location_dest_id': expired_product_type_id.default_location_dest_id.id,
                        })
                if sm_lines:
                    picking_values = {
                        'origin': 'Expired products %s' % (location.display_name),
                        'picking_type_id': expired_product_type_id.id,
                        'move_type': 'direct',
                        'state': 'draft',
                        'location_id': location.id,
                        'location_dest_id': expired_product_type_id.default_location_dest_id.id,
                    }
                    picking = self.env['stock.picking'].create(picking_values)
                    # necessary to make a second write otherwise the location_dest_id of the stock move will = the location_dest_id of the picking
                    picking.write({
                        'move_lines': [(0, 0, l) for l in sm_lines],
                    })

        if not cron_quants:
            return self.action_open_scrap_pickings(picking=picking)
        else:
            return picking

    @api.multi
    def action_open_scrap_pickings(self, picking=False):
        if picking:
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "view_type": "form",
                "view_mode": "form",
                "res_id": picking.id,
                "name": "Expired Products Picking",
            }
