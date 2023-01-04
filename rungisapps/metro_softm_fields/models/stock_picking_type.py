from odoo import models, fields


class MetroExtend_StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    softm_picking = fields.Boolean(string="SoftM Picking")
    softm_manual_transaction_reason = fields.Many2one(comodel_name='stock.inventory.line.reason')
    softm_manual_transaction_key = fields.Text(string="Softm Manual Transaction", related='softm_manual_transaction_reason.description')

    softm_manual_transaction = fields.Selection(
        selection=[
            ('601', 'Zugang'),
            ('600', 'Abgang')
        ]
    )    
    
    softm_automatic_transaction = fields.Selection(
        selection=[
            ('1', 'Zugang'),
            ('2', 'Abgang'),
            ('3', 'Umlagerung'),
        ]
    )
