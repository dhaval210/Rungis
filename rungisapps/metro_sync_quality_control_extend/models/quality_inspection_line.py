from odoo import api, fields, models


class QualityInspectionLine(models.Model):
    _inherit = 'quality.inspection.line'

    inspection_note = fields.Html(related="control_point_line_id.note")
