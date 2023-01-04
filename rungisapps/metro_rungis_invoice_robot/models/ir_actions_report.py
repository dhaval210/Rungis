from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @classmethod
    def _get_invoice_reports_ubl(cls):
        res = super(IrActionsReport, cls)._get_invoice_reports_ubl()
        res.append("metro_rungis_invoice_report.print_invoice")
        return res
