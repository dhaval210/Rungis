from odoo import _, api, models, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    picking_split_limit = fields.Integer(string="Picking Split Limit")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    picking_split_allow = fields.Boolean(string="Allow Picking Split", default=False, copy=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def split_single_pick(self, picking):
        if self.warehouse_id and self.warehouse_id.picking_split_limit:
            picking_split_limit = self.warehouse_id.picking_split_limit
            if len(picking.move_lines) > picking_split_limit:
                extra_moves = picking.move_lines[picking_split_limit:]
                if len(extra_moves)<= picking_split_limit:
                    new_picking = picking._create_split_pick()
                    new_picking._split_off_moves(extra_moves)
                else:                
                    for i in range(0, len(extra_moves), picking_split_limit):
                        new_picking = picking._create_split_pick()
                        new_picking._split_off_moves(extra_moves[i:i+picking_split_limit])

    @api.multi
    def _action_confirm(self):
        super(SaleOrder, self)._action_confirm()
        if self.partner_id.picking_split_allow:
            picking_ids = self.mapped('picking_ids')
            if picking_ids:
                for picking in picking_ids:
                    if picking.picking_type_id and picking.picking_type_id.code=='internal' and  'Pick' in  picking.picking_type_id.name:
                        self.split_single_pick(picking)
      

class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_splitpick = fields.Boolean(string="Splitted Pick", default=False, copy=False)

    def _create_split_pick(self, default=None):
        """Copy current picking with defaults passed, post message about new split picking created"""
        self.ensure_one()
        new_picking = self.copy(dict({
            'name': '/',
            'is_splitpick':True,
            'move_lines': [],
            'move_line_ids': [],
        }, **(default or {})))
        self.message_post(
            body=_(
                'The pick split <a href="#" '
                'data-oe-model="stock.picking" '
                'data-oe-id="%d">%s</a> has been done.'
            ) % (
                new_picking.id,
                new_picking.name
            )
        )
        return new_picking

    def _split_off_moves(self, moves):
        for move in moves:
            move.write({'picking_id': self.id})
            move.mapped('move_line_ids').write({'picking_id': self.id})
            move._action_assign()
        return True



 
class PickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    is_splitpick_batch = fields.Boolean(string="Splitted Pick", default=False, copy=False)