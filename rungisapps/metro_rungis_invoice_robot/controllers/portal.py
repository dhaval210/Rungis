import re
from odoo import http, _
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request, content_disposition


class EDIPortalAccount(PortalAccount):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        # Overwrite controller for /my/invoices/{invoice_id}, make pdf_ubl and xml files available
        # If a classic report_type is used, use the classic router
        if report_type in ('pdf', 'text', 'html'):
            return super(EDIPortalAccount, self).portal_my_invoice_detail(invoice_id, access_token, report_type, download, **kw)
        # Otherwise get the report
        try:
            invoice_sudo = self._document_check_access('account.invoice', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Render the report for it's given type
        if report_type in ('pdf_ubl', 'xml'):
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices', download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        PaymentProcessing.remove_payment_transaction(invoice_sudo.transaction_ids)
        return request.render("metro_rungis_invoice_robot.edi_portal_invoice_page", values)
        # return request.render("account.portal_invoice_page", values)

    def _show_report(self, model, report_type, report_ref, download=False):
        # Use classic functionality for classic report types
        if report_type in ('html', 'pdf', 'text'):
            return super(EDIPortalAccount, self)._show_report(model, report_type, report_ref, download)

        # Get the report with superuser rights
        report_sudo = request.env.ref(report_ref).sudo()

        if not isinstance(report_sudo, type(request.env['ir.actions.report'])):
            raise UserError(_("%s is not the reference of a report") % report_ref)

        # Variable which will hold the actual report
        cust_report = None
        # PDF with embedded XML
        if report_type == "pdf_ubl":
            method_name = "render_qweb_pdf"
            report = getattr(report_sudo, method_name)([model.id], data={'report_type': report_type})[0]
            cust_report = model.embed_ubl_xml_in_pdf(pdf_content=report, invoice=model)
        # Plain XML file
        elif report_type == "xml":
            cust_report = model.with_context({"active_ids": model.ids}).generates_ubl_xml_string()
        # Adjust HTTP headers
        reporthttpheaders = [
            ('Content-Type', 'application/pdf' if report_type == 'pdf_ubl' else 'text/xml'),
            # ('Content-Length', len(report)),
            ('Content-Length', len(cust_report)),
        ]
        # Generate file name
        if report_type in ('pdf_ubl', "xml") and download:
            filename = "%s.pdf" % (re.sub('\W+', '-', model._get_report_base_filename()))
            # Use UBL filename if type ubl, otherwise use PDF file name
            fn = filename if report_type == "pdf_ubl" else model.get_ubl_filename()
            reporthttpheaders.append(('Content-Disposition', content_disposition(fn)))
        # Return report to user
        return request.make_response(cust_report, headers=reporthttpheaders)
