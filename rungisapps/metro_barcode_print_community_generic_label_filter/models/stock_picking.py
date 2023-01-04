from odoo import models
import ast


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def call_pdf_report(self, line_ids=[], pdf=False, report_id='metro_barcode_print_community.action_print_product_labels'):

        get_param = self.env['ir.config_parameter'].sudo().get_param
        label_ids = get_param('metro_barcode_print_community_generic_label_filter.generic_label_ids')
        if label_ids is False or label_ids == 'res.generic.label()':
            return super().call_pdf_report(line_ids, pdf, report_id)
        else:
            generic_labels = self.env['res.generic.label'].browse(ast.literal_eval(label_ids))
            for generic_label in generic_labels:
                if generic_label.field_id.ttype == 'many2one':
                    field_value = self[generic_label.field_id.name].id
                else:
                    field_value = self[generic_label.field_id.name]

                if eval(str(field_value) + generic_label.condition + generic_label.value):
                    if pdf is True:
                        return super().call_pdf_report(line_ids, pdf, generic_label.report_id.xml_id)
                    super().call_pdf_report(line_ids, pdf, generic_label.report_id.xml_id)                    
        return True
