from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    grid_id = fields.Integer(string='')

    def action_open_grid_data(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'order.grid.report',
            'res_id': self.grid_id,
            'view_id': self.env.ref('metro_order_grid.order_grid_report_view_form_readonly').id,
            'view_mode': 'form',
            'target': 'main',
        }
