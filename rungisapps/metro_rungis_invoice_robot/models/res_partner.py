
from odoo import api, fields, models,_
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit='res.partner'
    
    transfert_mode = fields.Selection([
            ('mail','Mail'),
            ('portal', 'Portal'),
        ], string='Transportation Method',
        help=" * The Mail method will send the invoices to partners mail.\n"
        " * The Portal method will send the invoices to the portal account partner.\n",
        default="portal",
        )
    invoice_format = fields.Selection([
            ('pdf','PDF'),
            ('edi', 'EDI (UBL -> XML file)'),
            ('pdf_ubl', 'PDF (embedded UBL/XML)'),
        ], string='Invoice Format',
        help=" * The PDF format will send the invoice in normal format PDF.\n"
        " * The edi format will send the invoice in UBL/XML format.\n"
        " * The PDF (embedded UBL/XML) format will send the invoice UBL/XML embeded in PDF.",
        default="pdf",
        )
    
    portal = fields.Char(string='Portal', compute='_get_url_server',help="Link to access to Portal access")
    date_create_invoice = fields.Datetime(
        string='Invoice Creation Schedule',
        help='Date when to create & transfer',
        default=lambda self: fields.datetime.now())
    date_create_interval = fields.Integer(
        string="Invoice Creation Interval",
        help="Interval which is used to recalculate the 'Invoice Schedule Date' after it is expired",
        default=1
    )
    date_create_interval_unit = fields.Selection([
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        default="months"
    )


    def _get_url_server(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.portal= base_url + '/my/home'

    def shift_date_create_invoice(self, timestamp):
        self.ensure_one()
        # Do process until the schedule date is past the timestamp
        while timestamp > self.date_create_invoice:
            # Get delta from user
            delta = timedelta(
                days=self.date_create_interval if self.date_create_interval_unit == "days" else 0,
                weeks=self.date_create_interval if self.date_create_interval_unit == "weeks" else 0,
            )
            if self.date_create_interval_unit == "months":
                delta = relativedelta(months=self.date_create_interval)
            # Shift & store date
            newdate = self.date_create_invoice + delta
            self.date_create_invoice = newdate

    @api.one
    def _check_valid_process_controls(self):
        err = []
        if not self.transfert_mode:
            err.append("Transfer mode missing")
        if not self.invoice_format:
            err.append("Invoice format missing" )
        if not self.date_create_invoice:
            err.append("Invoice Creation Schedule missing")
        if not self.date_create_interval:
            err.append("Invoice Creation Interval missing")
        if not self.date_create_interval_unit:
            err.append("Invoice Creation Interval Unit missing (e.g. Days, Weeks, Months)")
        # Check transfer modes and make transfer mode dependent error checks
        if self.transfert_mode == "mail":
            if not self.email:
                err.append("Partner needs an email configured for transfer mode mail to work")
        # Return error without trailing newline
        return err
