from odoo import models, fields, api


class FishProductLabelsLine(models.TransientModel):
    _name = "fish.product.label.line"
    _description = 'Product Label Line'

    move_line_id = fields.Integer(
        string="Move Line",
        required=True,
    )
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True,
                                 domain="[('id', '=', product_id)]")
    pic_id = fields.Integer(string='Pick id')
    print_copy = fields.Integer(string='Copies')
    wizard_id = fields.Many2one('fish.product.label.report', string="Wizard")


class FishProductLabelsReport(models.TransientModel):
    _name = "fish.product.label.report"
    _description = 'Fish Product Label Report'

    product_label_moves = fields.One2many('fish.product.label.line', 'wizard_id')

    @api.multi
    def action_fish_product_label(self):
        move_datas = []
        for moves in self.product_label_moves:
            data = {
                'move_line_id': moves.move_line_id,
                'product_id': moves.product_id.id,
                'print_copy': moves.print_copy,
                'pic_id': moves.pic_id
            }
            move_datas.append(data)
        dict1 = {'product_label_moves': move_datas}
        action = self.env.ref('metro_rungis_fish_label_report.print_fish_report_pdf').report_action(self, data=dict1)
        action.update({'close_on_report_download': True})
        return action




