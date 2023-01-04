from odoo import models, fields


class MetroExtend_StockPicking(models.Model):
    _inherit = 'stock.picking'

    send_to_softm = fields.Boolean(string="SoftM Status", copy=False, default=False)
    softm_picking = fields.Boolean(
        string="SoftM Picking",
        related="picking_type_id.softm_picking"
    )

    # softm_manual_transaction = fields.Selection(
    #     related="picking_type_id.softm_manual_transaction"
    # )
    softm_manual_transaction_key = fields.Text(
        related="picking_type_id.softm_manual_transaction_key"
    )
    run_up_point = fields.Integer()
