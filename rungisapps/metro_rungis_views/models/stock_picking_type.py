from datetime import datetime

from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    count_picking_ready_today = fields.Integer(compute='compute_picking_today_count')

    def compute_picking_today_count(self):
        """
        Compute function for computing
        today having pickings as ready.

        """
        today = fields.Date.today()
        start = datetime(today.year, today.month, today.day, 0, 0, 0)
        end = datetime(today.year, today.month, today.day, 23, 55, 55)
        data = self.env['stock.picking'].read_group([('state', '=', 'assigned'), ('scheduled_date', '>=', start),
                                                     ('scheduled_date', '<=', end)] +
                                                    [('state', 'not in', ('done', 'cancel')),
                                                     ('picking_type_id', 'in', self.ids)],
                                                    ['picking_type_id'], ['picking_type_id'])
        count = {
            x['picking_type_id'][0]: x['picking_type_id_count']
            for x in data if x['picking_type_id']
        }
        for record in self:
            record['count_picking_ready_today'] = count.get(record.id, 0)

    def get_action_picking_tree_ready_today(self):
        return self._get_action('metro_rungis_views.action_picking_tree_ready_today')

    def get_action_picking_tree_draft(self):
        return self._get_action('metro_rungis_views.action_picking_tree_draft')


class MetroExtend_StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    special_wishes = fields.Char(string="Sonderwünsche", related='move_id.special_wishes')
