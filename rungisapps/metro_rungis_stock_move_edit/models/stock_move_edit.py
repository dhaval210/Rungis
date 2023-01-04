from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from datetime import datetime


class StockMoveEdit(models.Model):
    _name = "stock.move.edit"
    _description = 'Stock Move Edit'
    _inherit = 'mail.thread'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = []
        move_ids = []
        company_id = self.env.user.company_id

        if self.product_id:
             move_ids = self.env['stock.move'].search([('product_id','=',self.product_id.id),('price_unit','=',0.0),('remaining_qty','>',0.0),('company_id','=',company_id.id)])
        if move_ids:
            res = [(5,0,0)]
            for move in move_ids:
                move_data = {
                            'move_id': move.id,
                            'unit_price': move.price_unit,
                            'value': move.value,
                            'cost': self.product_id.standard_price,
                            'remaining_qty': move.remaining_qty,
                            'remaining_value': move.remaining_value,
                            'product_qty': move.product_qty,
                            'cw_product_qty': move.cw_product_qty,
                         }
                res.append(move_data)
        self.stock_move_edit_line_ids = res
        return

    product_id = fields.Many2one('product.template', string="Product", track_visibility='onchange',copy=False)
    stock_move_edit_line_ids = fields.One2many('stock.move.edit.line', 'move_edit_id', string="Stock Moves", track_visibility='onchange')#, default=_default_stock_moves)
    status = fields.Selection([('draft', 'Draft'), ('progress', 'In Progress'), ('cancel', 'Cancel'), ('done', 'Done')], string="Status", default='draft', track_visibility='onchange')
    date = fields.Datetime("Date", default=datetime.today())

    @api.multi
    def edit_data(self):
        for ids in self.stock_move_edit_line_ids:
            if ids.unit_price == 0:
                ids.unit_price = ids.cost
            if ids.cw_product_qty > 0:
                ids.value = ids.cost * ids.cw_product_qty
            else:
                ids.value = ids.cost * ids.product_qty
            if ids.remaining_value == 0:
                ids.remaining_value = ids.cost * ids.remaining_qty
        self.status = 'progress'

    @api.multi
    def cancel(self):
        self.status = 'cancel'
        return True

    @api.multi
    def update_moves(self):
        for move in self.stock_move_edit_line_ids:
            move.move_id.sudo().write({
                'price_unit': move.unit_price,
                'value': move.value,
                'remaining_value': move.remaining_value,
            })
        self.status = 'done'
        self.date = datetime.today()
        return True


class StockMoveEditWizardLine(models.Model):
    _name = "stock.move.edit.line"
    _description = 'Stock Move Edit Line'
    _inherit = 'mail.thread'

    move_edit_id = fields.Many2one('stock.move.edit', string="Stock Moves")
    move_id = fields.Many2one('stock.move', string='Stock Moves')
    unit_price = fields.Float("Unit Price", track_visibility='onchange')
    value = fields. Float('Value', track_visibility='onchange')
    cost = fields.Float('Product Cost')
    remaining_qty = fields.Float('Remaining Qty')
    remaining_value = fields.Float('Remaining Value', track_visibility='onchange')
    product_qty = fields.Float('Real Qty')
    cw_product_qty = fields.Float('Real CW Qty')

