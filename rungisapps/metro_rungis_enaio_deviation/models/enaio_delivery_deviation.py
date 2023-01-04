from odoo import api, fields, models
from datetime import datetime
import zipfile
import base64
import io
from odoo.exceptions import ValidationError


class EnaioDeliveryDeviation(models.Model):
    _name = 'enaio.delivery.deviation'
    _description = 'Enaio Delivery Deviation'
    _inherit = 'mail.thread'

    deviation_zipfile = fields.Binary("Upload Deviation Zipfile", track_visibility='onchange', help='Please upload zip files only')
    file_name = fields.Char('File Name', track_visibility='onchange')
    upload_date = fields.Datetime("Date", default=datetime.today())
    status = fields.Selection([('draft', 'Draft'), ('error', 'File Error'), ('done', 'Deviation Uploaded'), ('cancel', 'Cancelled')], readonly=True, default="draft", track_visibility='onchange')
    log_file = fields.Text("Log File")
    error_check = fields.Boolean("Error Check", default=False)

    @api.multi
    def cancel(self):
        self.status = 'cancel'
        return True

    @api.multi
    def _get_enaio_remark_id(self,code):
        remark_id = self.env['enaio.deviation.remark'].search([('name', '=', code)])
        if remark_id:
            return remark_id.id
        else:
            return False

    @api.multi
    def upload_delivery_deviation(self):
        if self.deviation_zipfile and self.file_name:
            if not '.zip' in self.file_name:
                raise ValidationError('File should be of .zip extension.!')

            binary_file = base64.decodestring(self.deviation_zipfile)
            zfile = io.BytesIO(binary_file)
            files = zipfile.ZipFile(zfile, "r")
            self.log_file = ""
            self.error_check=False
            for name in files.namelist()[1:]:#Ignore the first file in the zip because it is a folder that contains the actual .csv files
                if not '.csv' or not '.CSV' in name:
                    raise ValidationError('Files in the zip folder should be of .csv extension.!')
                data = (files.read(name)).decode("utf-8")
                if ',' in data:
                    data = data.replace(',','.')
                data = data.split()
                #company~SO number~Position~Delivery Number~Product Int Ref~NA~Discount~Remark Ref~Qty Diff~Accepted Qty~Accepted CW Qty
                #data = 01~2412184~4~6025106~4137~3.080~0~10~-1.000~1.000~3.080

                for datas in data:
                    data_list = datas.split('~')
                    so_name='SO'+data_list[1]
                    comp_id = self.env["ir.config_parameter"].sudo().get_param(
                        "metro_rungis_enaio_deviation.enaio_deviation_company_parameter")
                    if comp_id:
                        company_id = self.env['res.company'].search([('id', '=', comp_id)])
                    else:
                        raise ValidationError('Please contact System Admin to set up Company parameter..!!')
                    so_id = self.env['sale.order'].search([('name','=',so_name),('company_id','=',company_id.id)])
                    product_id = self.env['product.product'].search([('default_code','=',data_list[4])])

                    if data_list[8]!=0.0 and data_list[6]!=0.0 and so_id and product_id:
                        for pickings in so_id.picking_ids:
                            if pickings.state == 'assigned' and pickings.picking_type_id.code == 'outgoing':
                                ##pickings.action_pack_operation_auto_fill()
                                for moves in pickings.move_line_ids:
                                    if moves.product_id == product_id and moves.product_uom_qty:
                                        moves.qty_done = data_list[9]
                                        moves.enaio_remark_id = self._get_enaio_remark_id(data_list[7])
                                        if product_id.catch_weight_ok:
                                            moves.cw_qty_done = data_list[10]
                        so_line_id = self.env['sale.order.line'].search(
                            [('delivery_no', '=', data_list[3]), ('order_id', '=', so_id.id),
                             ('product_id', '=', product_id.id), ('so_pos_no', '=', data_list[2])])
                        if so_line_id:
                            so_line_id.discount = data_list[6]
                            so_line_id.enaio_remark_id = self._get_enaio_remark_id(data_list[7])
                            self.log_file = self.log_file + " \r\n " + "File " + str(name) + " - Delivery Deviation updated for Sale Order: " + str(so_name) + " for Product: " + str(product_id.default_code)
                        else:
                            self.log_file = self.log_file + " \r\n " + "File " + str(name) + " - Sale Order: " + str(
                                so_name) + " / Product: " + str(data_list[4]) + " with position number" + str(data_list[2]) + " not found..!! Hence Discount% not updated"
                    else:
                        if not so_id or not product_id:
                            self.log_file = self.log_file + " \r\n " + "File " + str(name) + " - Sale Order: " + str(so_name) + " / Product: " + str(data_list[4]) + "  not found..!!"
                            self.error_check = True

            if not self.error_check:
                self.status = 'done'
            else:
                self.status = 'error'




