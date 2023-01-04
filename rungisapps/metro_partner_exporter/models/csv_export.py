from odoo import api, fields, models


class CsvExport(models.Model):
    _name = 'csv.export'
    _order = "export_date desc"

    name = fields.Char(string='CSV exports')
    export_date = fields.Datetime(string='Export Date')
    exported_file = fields.Binary(string='Exported File')
    backend_id = fields.Many2one('csv.backend')

