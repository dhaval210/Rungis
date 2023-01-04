from odoo import api, models
from odoo.osv import expression
from odoo.tools.misc import split_every
from odoo.addons.queue_job.job import job

from itertools import groupby
from operator import itemgetter

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _get_moves_to_assign_domain(self, company_id):
        block_types_ids = self.env['stock.picking.type'].search([
            ('block_stock_assignment', '=', True)
        ])
        if len(block_types_ids) > 0:
            moves_domain = expression.AND([
                [('state', 'in', ['confirmed', 'partially_available'])],
                [('product_uom_qty', '!=', 0.0)],
                [('picking_type_id', 'not in', block_types_ids.ids)]
            ])
        else:
            moves_domain = expression.AND([
                [('state', 'in', ['confirmed', 'partially_available'])],
                [('product_uom_qty', '!=', 0.0)]
            ])
        if company_id:
            moves_domain = expression.AND([[('company_id', '=', company_id)], moves_domain])
        return moves_domain

    def reset_operation_shipping_policy(self):
        async_type_ids = self.env['stock.picking.type'].search([
            ('async_reservation', '=', True),
        ])
        if len(async_type_ids) > 0:
            for ati in async_type_ids:
                # reset at the end of the day to "procurement_group" // configurable?
                ati.shipping_policy = "force_all_products_ready"

    def async_reservation_scheduler(self):
        async_type_ids = self.env['stock.picking.type'].search([
            ('async_reservation', '=', True),
            ('block_stock_assignment', '=', False)
        ])
        if len(async_type_ids) > 0:
            for ati in async_type_ids:
                if ati.reservation_progress > 0:
                    continue
                # Param = self.env['ir.config_parameter']
                # whin_is_done = Param.sudo().get_param('metro_procurement_manager.whin_is_done')
                # if whin_is_done is True and ati.shipping_policy != "force_as_soon_as_possible":
                #     ati.shipping_policy = "force_as_soon_as_possible"
                #     domain = expression.AND([
                #         [('state', 'in', ['confirmed'])],
                #         [('picking_type_id', '=', ati.id)],
                #         [('shipping_policy', '=', 'one')]
                #     ])
                #     pickings = self.env['stock.picking'].search(domain)
                #     pickings.write({
                #         'shipping_policy': 'direct'
                #     })
                self.with_delay(eta=2).run_specific_move_assign(ati)

    @api.model
    @job(default_channel='root.reserve_tour')
    def run_specific_move_assign(self, type_id, use_new_cursor=False):
        domain = expression.AND([
            [('state', 'in', ['confirmed', 'partially_available', 'assigned'])],
            [('picking_type_id', '=', type_id.id)]
        ])
        moves_to_assign = self.env['stock.move'].search(domain, limit=None,
            order='priority desc, date_expected asc')

        picking_ids = moves_to_assign.mapped('picking_id')
        self.reserve_tour(picking_ids, type_id)
        self.env.cr.commit()
        type_id.reservation_progress = 0

    @job(default_channel='root.reserve_tour')
    def reserve_tour(self, pick_ids, type_id, k0=False, k1=False):
        domain = expression.AND([
            [('state', 'in', ['confirmed', 'partially_available'])],
            [('picking_id', 'in', pick_ids)]
        ])
        moves_to_assign = self.env['stock.move'].search(domain, limit=None,
            order='priority desc, date_expected asc')
        for moves_chunk in split_every(100, moves_to_assign.ids):
            self.env['stock.move'].browse(moves_chunk)._action_assign()
