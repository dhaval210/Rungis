from odoo import api, models
from odoo.osv import expression
from odoo.tools.misc import split_every

from itertools import groupby
from operator import itemgetter
from odoo.addons.queue_job.job import job


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

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

        # group pickings by type & tour
        keys_in_groupby = ['picking_type_id', 'transporter_route_id']
        bunch_pickings = {}
        picking_ids = picking_ids.sorted(key=lambda r: r.transporter_route_id.id)
        for k, g in groupby(picking_ids, key=itemgetter(*keys_in_groupby)):
            pick_ids = [pick.id for pick in g]
            k0 = k[0].id
            k1 = k[1].id
            if k1 is False:
                bunch_pickings.update({
                    k0: []
                })
                bunch_pickings[k0] += pick_ids
                continue
            self.reserve_tour(pick_ids, type_id, k0, k1)
            self.env.cr.commit()
        if len(bunch_pickings) > 0:
            for key, bps in bunch_pickings.items():
                type_id.reservation_progress += 1
                self.reserve_tour(bps, type_id, key, False)
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
        # self._cr.commit()

        pickingids = self.env['stock.picking'].browse(pick_ids).filtered(
            lambda p: (
                p.batch_id.id is False and
                p.state == 'assigned' and
                p.picking_type_id.allow_batch_assignment is True and
                p.partner_id.kac is False
            )
        ).sorted(
            key=lambda r: r.run_up_point,
            reverse=True
        )
        if len(pickingids) > 0:
            p_ids = [pick.id for pick in pickingids]
            batch = self.env['stock.picking.batch'].search(
                [
                    ('user_id', '=', False),
                    ('use_voice_pick', '=', True),
                    ('state', '=', 'in_progress'),
                    ('type_id', '=', k0),
                    ('group_id', '=', k1),
                ],
                limit=1
            )
            if batch.id is not False:
                batch.write({
                    'picking_ids': [[4, p] for p in p_ids]
                })
            else:
                batch = self.env['stock.picking.batch'].create({
                    'use_voice_pick': True,
                    'picking_ids': [[6, 0, p_ids]],
                    'type_id': k0,
                    'group_id': k1,
                })
                batch.confirm_picking()
