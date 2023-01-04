from odoo import models, api
import ast
from odoo.addons.metro_barcode_print_community.models.stock_picking import Picking as SP

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def print_fishproduct_label(self):
        """ while clicking print fish product label,function used to pass value to wizard"""
        product_list = []
        ref_data = self.env['ir.config_parameter'].sudo().get_param('fish_product_category_name')
        for res in self.move_line_ids:
            for line in res.product_id.categ_ids:
                if line.name == ref_data:
                    if self.state == 'assigned':
                        product_list.append((0, 0, {
                            'move_line_id': res.id,
                            'product_id': res.product_id.id,
                            'print_copy': res.product_uom_qty,
                            'pic_id': self.id
                        }))
                    else:
                        product_list.append((0, 0, {
                            'move_line_id': res.id,
                            'product_id': res.product_id.id,
                            'print_copy': res.qty_done,
                            'pic_id': self.id
                        }))

        return {
            'name': 'Print Fish product labels',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'fish.product.label.report',
            'target': 'new',
            'context': {
                'default_product_label_moves': product_list,
            },
        }

    def call_pdf_report(self, line_ids=[], pdf=False, report_id='metro_barcode_print_community.action_print_product_labels'):
        move_datas = []
        ref_data = self.env['ir.config_parameter'].sudo().get_param('fish_product_category_name')
        piece_fish_operation_types = self.env['ir.config_parameter'].sudo().get_param('metro_rungis_fish_label_report.piece_fish_operation_type_ids')
        piece_fish_operation_types = ast.literal_eval(piece_fish_operation_types)

        if len(piece_fish_operation_types) > 0 and self.picking_type_id.id in piece_fish_operation_types:
            for res in self.move_line_ids.filtered(lambda r: r.id in line_ids):
                if res.qty_done > 0:
                    for line in res.product_id.categ_ids:
                        if line.name == ref_data:
                            data = {
                                'move_line_id': res.id,
                                'product_id': res.product_id.id,
                                'print_copy': res.qty_done,
                                'pic_id': self.id
                            }
                            move_datas.append(data)
        else:
            for res in self.move_line_ids.filtered(lambda r: r.id in line_ids):
                if res.qty_done > 0:            
                    data = {
                        'move_line_id': res.id,
                        'product_id': res.product_id.id,
                        'print_copy': res.qty_done,
                        'pic_id': self.id
                    }
                    move_datas.append(data)

        if len(move_datas) > 0:
            dict1 = {'product_label_moves': move_datas}
            if not pdf:
                self.env.ref(report_id).render_qweb_pdf(
                    res_ids=[self.id],
                    data=dict1
                )
                return True
            else:
                return self.env.ref(report_id).report_action(self, data=dict1)

    SP.call_pdf_report = call_pdf_report
