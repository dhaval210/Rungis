from odoo.addons.component.core import AbstractComponent
from odoo import fields
import logging
_logger = logging.getLogger(__name__)
import csv
import io
import base64


class CSVAdapter(AbstractComponent):
    _name = 'csv.adapter'
    _inherit = ['base.backend.adapter', 'base.csv.connector']
    _usage = 'backend.adapter'
    _file_name = 'csv'
    _file_header = []

    def _call(self, action=None, record_list=None):
        if record_list:
            if action == 'create':
                header = True
                fobj = io.StringIO()
                writer = csv.writer(fobj, delimiter='\t')
                for record in record_list:
                    values_list = []
                    if header:
                        columns = self._file_header
                        writer.writerow(columns)
                    for column in columns:
                        try:
                            values_list += [record[column]]
                        except:
                            values_list += ['']
                    writer.writerow(values_list)
                    header = False
            obj_retval = fobj.getvalue()
            now = fields.Datetime.now()
            if self.backend_record.export_to_disk:
                with open(self.backend_record.path + '/{0}_{1}'.format(self._file_name,now.strftime("%Y%m%d%H%M%S")), 'w') as f:
                    f.write(obj_retval)
            data_bytes = obj_retval.encode("utf-8")
            self.env['csv.export'].create({'name':'{0}_{1}.csv'.format(self._file_name,now.strftime("%Y%m%d%H%M%S")),'export_date':now,
                                           'backend_id': self.backend_record.id, 'exported_file': base64.b64encode(data_bytes)})
            fobj.close()


    def create(self, record_list):
        return self._call('create', record_list=record_list)

