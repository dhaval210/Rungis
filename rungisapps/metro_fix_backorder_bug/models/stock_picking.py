from odoo import api, _
from odoo.addons.stock.models.stock_picking import Picking as SP


@api.multi
def _create_backorder(self, backorder_moves=[]):
    """ Move all non-done lines into a new backorder picking.
    """
    backorders = self.env['stock.picking']
    for picking in self:
        moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
        if moves_to_backorder:
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'move_line_ids': [],
                'backorder_id': picking.id
            })
            picking.message_post(
                body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                    backorder_picking.id, backorder_picking.name))
            moves_to_backorder.write({'picking_id': backorder_picking.id})
            # bug line odoo core
            # moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})

            # fix
            move_lines_ids = moves_to_backorder.mapped('move_line_ids')
            for mli in move_lines_ids:
                mli.package_level_id.write({'picking_id': backorder_picking.id})
            # end of fix

            moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
            backorder_picking.action_assign()
            backorders |= backorder_picking
    return backorders


SP._create_backorder = _create_backorder
