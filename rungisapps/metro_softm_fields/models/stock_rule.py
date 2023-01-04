from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += [
            'tour_id',
            'process_position',
            'process_number',
            'special_wishes'
        ]
        return fields
