from odoo import api, fields, models


class CsvExport(models.Model):
    _inherit = 'csv.export'

    def get_last_file(self):
        """ getting last updated record and add it to attachement if the attachment is not created """
        last_id = self.search([], limit=1, order='write_date desc')
        for rec in last_id:    
            attach = self.env['ir.attachment'].with_context(ctx).create({
                        'name': '{0}_{1}.csv'.format(rec.name,now.strftime("%Y%m%d%H%M%S")),
                        'res_id': rec.id,
                        'res_model': 'csv.export',
                        'datas': base64.b64encode(rec.exported_file),
                        'datas_fname': '{0}_{1}.csv'.format(rec.name,now.strftime("%Y%m%d%H%M%S")),
                        'type': 'binary',
                        'public': 'True',
                        'data_to_transfert': 'True'
                        })   
