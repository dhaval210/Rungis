from odoo import _, api, models, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.osv import expression
from odoo.tools.misc import split_every
from odoo.addons.queue_job.job import job


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

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


        splited_picking_ids = pickingids.filtered(lambda p: p.is_splitpick is True)
        remaining_picks = pickingids.filtered(lambda p: p.is_splitpick is False)
        
        if len(remaining_picks) > 0:
            p_ids = [pick.id for pick in remaining_picks]
            batch = self.env['stock.picking.batch'].search(
                [
                    ('user_id', '=', False),
                    ('use_voice_pick', '=', True),
                    ('is_splitpick_batch', '=', False),
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

        if len(splited_picking_ids) > 0:
            for split_pick in splited_picking_ids:
                batch = self.env['stock.picking.batch'].create({
                    'use_voice_pick': True,
                    'is_splitpick_batch': True,
                    'picking_ids': [[6, 0, [split_pick.id]]],
                    'type_id': k0,
                    'group_id': k1,
                })
                batch.confirm_picking()