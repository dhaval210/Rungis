from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        super()._process(cancel_backorder=True)
        for pick_id in self.pick_ids:
            if pick_id.picking_type_code == 'incoming':
                template = self.env.ref(
                    'metro_backorder_notification.stock_backorder_mail'
                )
                for bo_id in pick_id.backorder_ids.ids:
                    self.env['mail.template'].browse(template.id).send_mail(bo_id)
