from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    allow_block = fields.Boolean()
    block_stock_assignment = fields.Boolean()
    async_reservation = fields.Boolean()
    reservation_progress = fields.Integer()

    def set_whin_true(self):
        ir_params = self.env['ir.config_parameter'].sudo()
        ir_params.set_param('metro_procurement_manager.whin_is_done', True)

    def set_whin_false(self):
        ir_params = self.env['ir.config_parameter'].sudo()
        ir_params.set_param('metro_procurement_manager.whin_is_done', False)

    def toggle_block_stock_assignment(self):
        for rec in self:
            rec.block_stock_assignment = not rec.block_stock_assignment
            if rec.block_stock_assignment is False:
                rec.run_specific_move_assign()
            else:
                rec.reservation_progress = 0

    def run_specific_move_assign(self):
        self.block_stock_assignment = False
        procure = self.env['procurement.group']
        self.reservation_progress = 1
        procure.with_delay(eta=2).run_specific_move_assign(self)
