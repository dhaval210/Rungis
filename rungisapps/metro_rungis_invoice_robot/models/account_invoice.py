import base64
import logging
import itertools
import operator

from odoo.addons.queue_job.job import job
from odoo.osv.orm import browse_record, browse_null
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

from datetime import datetime


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    
    picking_invoice = fields.Boolean('invoice created from picking', default=False)
    
    state = fields.Selection([
            ('draft','Draft'),
            ('sent','Sent to responsible'),
            ('passed','passed error validation'),
            ('open', 'Open'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('merged', 'Merged into Collective'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
         help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.\n"
             " * The 'passed' status is used when the robot or responsible validate and check erroe in invoice data.\n"
             " * The 'merged' status is used when the robot has merged single invoices into collective invoices.\n"
             " * The 'sent' status is used when The robot finds some error and sent the invoice to the responsible to check it.")
    is_merged = fields.Boolean('Merged Invoice', default=False)
    # Overwrite invoice_line_ids of account module, goal is to make the invoice line editable when state is in sent
    invoice_line_ids = fields.One2many('account.invoice.line', 'invoice_id', string='Invoice Lines', oldname='invoice_line',
        readonly=True, states={'draft': [('readonly', False)], 'sent': [("readonly", False)]}, copy=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [("readonly", False)]},
        help="If you use payment terms, the due date will be computed automatically at the generation "
            "of accounting entries. If you keep the payment terms and the due date empty, it means direct payment. "
            "The payment terms may compute several due dates, for example 50% now, 50% in one month.")
    comment = fields.Text('Additional Information', copy=True, readonly=True, states={'draft': [('readonly', False)],'sent': [("readonly", False)]})

    
    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state not in ('draft','passed')):
            raise UserError(_("Invoice must be in draft or passed state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(_('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    def passe_error_validation(self):
        for rec in self:
            rec.write({'state':'passed'})
            rec._set_order_invoiced()

    @api.multi    
    def _set_order_invoiced(self):
        for rec in self:
            sale_id = self.env["sale.order"].search([("name", "=", rec.origin)])
            if not sale_id:
                logger.warn("No Sale Order found for {} with origin {}.".format(rec.id, rec.origin))
                continue
            sale_id.write({"invoice_status": "invoiced"})
    
    @api.multi
    def action_mark_errorprone(self):
        for r in self:
            if r.state == "passed":
                r.write({"state": "sent"})

    @api.multi
    def action_invoice_merged(self):
        for invoice in self:
            # Don't overwrite the state for draft or error-prone invoices
            if invoice.state in ("draft", "sent"):
                continue
            invoice.write({"state": "merged"})

    @api.one
    def _pre_process_invoice(self):
        """This function takes a draft invoice and processes it into the states "passed error validation" or "Sent to Responsible".

        Returns:
            bool: True if invoice was processed successfully, False if not
        """
        try:
            # Check invoice for errors, post them if errors were found and continue with next picking, for some reason it's returned as a list
            # maybe this is caused by @api.one?
            msg = self._check_invoice_errors()[0]
            # Compute values for invoice
            self.compute_taxes()
            self._set_global_discounts_by_tax()
            self._compute_amount()
            if msg != "":
                self.message_post(body=msg)
                self.write({"state": "sent"})
                # send error-prone invoice to responsible
                self.send_invoice_mail_error()
                self.env.cr.commit()
                return True
            # Invoice is error-free
            self.write({'state':'passed',})
            self._set_order_invoiced()
            self.env.cr.commit()
        except Exception as e:
            # Log error in logs
            logger.warning("Failed to process invoice {} ({}):\n{}".format(self.number, self.id, e))
            # Post error into the chatter
            msg = "WARNING: Failed to process invoice {} ({}):\n{}".format(self.number, self.id, e)
            self.message_post(body=msg)
            return False
        return True

    @api.multi
    def attach_pdf_file_to_send(self, partner):
        """
            creating attachement report to send to partner, optionally with embedded UBL
        """
        # Attachment file and UBL content should be added with this function via odoo base & invoice_ubl
        file_id = self.env.ref('account.account_invoices').render_qweb_pdf([self.id])[0]
    
        attach = self.env["ir.attachment"].search([
            ("res_model", "=", "account.invoice"),
            ("res_id", "=", self.id),
        ], order="id asc")
        # If initial attachment failed, use this as fallback
        if not attach:
            logger.warning("No attachment found for partner {}, create custom one.".format(partner.name))
            name = self.number if self.number and self.number.endswith("pdf") else self.number + ".pdf"
            # If PDF should contain UBL XML, insert it into PDF
            if partner.invoice_format == 'pdf_ubl':
                file_id = self.embed_ubl_xml_in_pdf(pdf_content=file_id, invoice=self)
            ctx = dict()
            attach = self.env['ir.attachment'].with_context(ctx).create({
                'name': name,
                'res_id': self.id,
                'res_model': str(self._name),
                'datas': base64.b64encode(file_id),
                'datas_fname': name,
                'type': 'binary',
                'public': True,
                'to_transfert': True,
                'data_to_transfert': True,
            })

        return attach

    @api.multi
    def attach_ubl_xml_file_to_send(self, partner):
        """
            creating attachement EDI, UBL w/ embedded PDF to send to partner
        """
        version = self.get_ubl_version()
        no_embedded_pdf = True if partner.invoice_format == 'edi' else False
        # ubl invoices
        xml_string = self.with_context(no_embedded_pdf=no_embedded_pdf).generate_ubl_xml_string(version=version)
            
        filename = self.get_ubl_filename(version=version)
        
        ctx = {}
        attach = self.env['ir.attachment'].with_context(ctx).create({
            'name': filename,
            'res_id': self.id,
            'res_model': str(self._name),
            'datas': base64.b64encode(xml_string),
            'datas_fname': filename,
            'type': 'binary',
            'public':True,
            'to_transfert': True,
            'data_to_transfert': True,
        })
        return attach

    @api.multi
    def send_invoice_mail_error(self):
        """
            Function to send Error prone invoice to responsible used in creation and checing robot
        """
        lang = self.env.user.lang
        email_values = {'email_to': self.user_id.email,
                        'email_from': self.env.user.email}
        template = self.env.ref('metro_rungis_invoice_robot.mail_template_invoice_error')
        template.with_context(lang=lang).send_mail(self.id, email_values=email_values, force_send=True)
        return True

    @api.multi
    def send_invoice_mail(self, partner):
        """
             action to send invoice via mail to partner
        """
        partner = self.partner_id
        
        template = None
        data_id = self.generate_attachment_file(partner)

        # If not portal it's mail (if not overwritten by 3rd module)
        if  partner.transfert_mode != 'portal':
            template = self.env.ref('metro_rungis_invoice_robot.mail_template_invoice')
        elif partner.transfert_mode == 'portal':   
            template = self.env.ref('metro_rungis_invoice_robot.mail_template_invoice_portal')

        template.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {'email_to': partner.email,
                        'email_from': self.env.user.email}

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        my_url = "/my/invoices/{}".format(self.id)
        portal_url = base_url + my_url

        # FIXME: This line throws an error after the change, looks like some email is created at this point (only when swiss localization is installed) => RUN-1286
        # File "/usr/lib/python3/dist-packages/odoo/addons/l10n_ch/models/mail_template.py", line 56, in generate_email
        #     rslt[res_id]['attachments'] = new_attachments
        # KeyError: 525
        template.with_context(portal_url=portal_url).send_mail(self.id, email_values=email_values, force_send=True)
        return True
    
    def generate_attachment_file(self, partner):
        data_id = None
        # PDF w/ or w/o embedded XML
        if partner.invoice_format == 'pdf' or partner.invoice_format == 'pdf_ubl':    
            data_id = self.attach_pdf_file_to_send(partner)
        # XML file only
        elif partner.invoice_format == 'edi':
            data_id = self.attach_ubl_xml_file_to_send(partner)
        return data_id
    
    @api.multi
    def merge_invoices(self):
        """2nd cron job of the robot, merge invoices per partner

        Returns:
            bool: True if merge of invoices was successful
        """
        #partner = self.partner_id
        timestamp = datetime.now()
        company_ids = self.env["res.company"].search([("run_invoice_robot", "=", True)])
        for company in company_ids:
            logger.debug("Start merging invoices with company %s!" % company.name)
            # Get passed invoices from the current company
            invoices = self._get_passed_invoices(company)
            # Only do invoices where the partner's invoice create date lays in past
            invoices = invoices.filtered(lambda i: timestamp > i.partner_id.date_create_invoice)
            invs_sorted = sorted(invoices, key=lambda x:x.partner_id.id)
            # pass invoices grouped by partner to async jobs
            for partner_id, invoice_group in itertools.groupby(invs_sorted, key=operator.itemgetter('partner_id')):
                job_desc = partner_id.name + ' merge invoices'
                invoice_ids = [invoice.id for invoice in invoice_group]
                invs = self.browse(invoice_ids)
                self.with_delay(description=job_desc).async_merge_invoices(invs, company)
        return True

    @job(default_channel='root.merge_invoices')
    def async_merge_invoices(self, invoices, company):
        """Asynchronous function to generate merged invoices per partner, will be called by merge_invoicess

        Args:
            invoices (list): list of account.invoice's to be merged per partner
            company (res.company): company the invoices are created for
        """
        timestamp = datetime.now()
        invoices.do_merges(keep_references=True,
                            date_invoice=self.date_invoice,
                            company=company,
                            manually_selected=True)

        # merged_invoices = invoices.filtered(lambda i: i.is_merged is True and i.sent is False)
        merged_invoices = self.search([
            ('is_merged','=',True),
            ("company_id", "=", company.id),
            # Only get invoices which are not send yet
            ("state", "=", "passed")
        ])

        for inv in merged_invoices:
            # Validation of the merged invoices
            inv.action_invoice_open()
            inv.partner_id.shift_date_create_invoice(timestamp)
            self.env.cr.commit()

    @api.model
    def send_invoices(self):
        """3rd cron for sending merged invoices to partners
        """
        company_ids = self.env["res.company"].search([("run_invoice_robot", "=", True)])
        for company in company_ids:
            # Make sure to only get merged invoices that are not sent and in the current company
            # merged_invoices = self.filtered(lambda i: i.is_merged is True and i.sent is False and i.company_id.id == company.id)
            merged_invoices = self.search([
                ('is_merged','=',True),
                ("company_id", "=", company.id),
                # Only get invoices which are not send yet
                ("state", "=", "open"),
                ("sent", "=", False)
            ])
            for inv in merged_invoices:
                # Check partner for errors before merging invoices
                err = inv.partner_id._check_valid_process_controls()[0]
                if len(err) > 0:
                    logger.warn("There was an error with the contact {} ({})".format(inv.partner_id.name, inv.partner_id.id))
                    msg = "<p>There were some errors while trying to generate invoices for this partner:</p><ul>"
                    for e in err:
                        msg += "<li>" + e + "</li>"
                    msg += "</ul>"
                    # Post error message on each invoice of the partner
                    inv.message_post(body=msg)
                    continue

                job_desc = inv.partner_id.name + " send merged invoice"
                self.with_delay(description=job_desc).async_send_invoices(inv)

    @job(default_channel='root.send_invoices')
    def async_send_invoices(self, invoice):
        """Asynchronous function to send merged invoices to each partner, might be overwritten by submodules

        Args:
            invoice (account.invoice): Merged invoice to be sent to the partner
        """
        invoice.send_invoice_mail(invoice.partner_id)
        invoice.sent = True
        self.env.cr.commit()

    @api.model
    def _get_first_invoice_fields(self, invoice):
        return {
            'origin': '%s' % (invoice.origin or '',),
            'partner_id': invoice.partner_id.id,
            'journal_id': invoice.journal_id.id,
            'user_id': invoice.user_id.id,
            'currency_id': invoice.currency_id.id,
            'company_id': invoice.company_id.id,
            'type': invoice.type,
            'account_id': invoice.account_id.id,
            'state': 'passed',
            'reference': '%s' % (invoice.reference or '',),
            'name': '%s' % (invoice.name or '',),
            'fiscal_position_id': invoice.fiscal_position_id.id,
            'payment_term_id': invoice.payment_term_id.id,
            'invoice_line_ids': {},
            'partner_bank_id': invoice.partner_bank_id.id,
            'comment':invoice.comment,
        }

    @api.one
    def _check_invoice_errors(self):
        """Checks the given invoice, its invoice linesand its partner for errors and returns them if errors are existing.

        Returns:
            str: List of errors expressed as a formatted HTML string
        """
        self.ensure_one()
        message = ""
        # Check general errors on invoice
        if self.id:
            # Missing payment terms
            if self.payment_term_id.id == False:
                message += _("- Missing payment terms on invoice {} ({}).<br />".format(self.name, self.id))
            # Customer is not set as comany
            if not self.partner_shipping_id.id or self.partner_shipping_id.id and self.partner_shipping_id.company_type != "company":
                message += _("- The partner {} ({}) on invoice {} is not from type 'Company'.<br />".format(self.partner_id.name, self.partner_id.id, self.name))
            # Invoice address is not set as company, or not as invoice address
            if self.partner_id.company_type != "company" or self.partner_id.type != "invoice":
                message += _("- The invoice partner {} ({}) on invoice {} is either not set to Company (currently: '{}') or not set to Invoice Address (currently: '{}')<br />"
                            .format(self.partner_id.name, self.partner_id.id, self.name, self.partner_id.company_type, self.partner_id.type))
            # Missing global discount
            if len(self.global_discount_ids.ids) == 0:
                message += _("- No Global Discounts set on Invoice {} ({}).<br />".format(self.name, self.id))
            else:
                # Deviating global discounts from partner (Sale Order partner)
                if sorted(self.global_discount_ids.ids) != sorted(self.partner_shipping_id.customer_global_discount_ids.ids):
                    message += _("- Global Discounts on Invoice {} ({}) differ from global discounts defined on partner {}.<br />".format(self.name, self.id, self.partner_shipping_id.name))
        # Check errors for each invoice line
        for line in self.invoice_line_ids:
            # Check price
            if line.price_unit <= 0.10 or (line.price_unit >= 999.0 and line.price_unit < 1000.0):
                message += _("- The price is not well set: " + str(line.price_unit) + ".<br />")
            # Missing taxes
            if not line.invoice_line_tax_ids:
                message += _("- The tax is not set.<br/>")
            # Missing HS Code
            if not line.product_id.hs_code_id:
                message += _("- The HS_Code is not set for product {}.<br/>".format(line.product_id.name))
            # Missing CWUOM if product is a catchweight product
            if line.product_id._is_cw_product() and line.product_id.cw_uom_id.id == False:
                message += _("- The product {} is a Catch Weight product but has no CW UoM set.<br />".format(line.product_id.name))
            # Fake taxes 
            if line.invoice_line_tax_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.is_fake:
                        message += _("- The tax {} is marked as a fake tax.<br/>".format(tax.name))
                        break
        return message

    @api.multi
    def _get_passed_invoices(self, company=None):
        """Overridable function to return passed invoices to merge"""
        domain = [
            ('state','=','passed'),
            # ('picking_invoice','=',True),
        ]
        if company:
            domain.append(("company_id", "=", company.id))
        return self.search(domain)

    @api.model
    def _get_invoice_key_cols(self):
        # TODO: Add docs
        res = super(AccountInvoice, self)._get_invoice_key_cols()
        res.append("global_discount_ids")
        res.remove('user_id')
        return res

    # FIXME: Probably whole function can be optimized (storage & performance)
    @api.multi
    def do_merges(self, keep_references=True, date_invoice=False,
                 remove_empty_invoice_lines=True, company=None, manually_selected=False):
        """
        To merge similar type of account invoices.
        Invoices will only be merged if:
        * Account invoices are in passed
        * Account invoices belong to the same partner
        * Account invoices are have same company, partner, address, currency,
          journal, currency, salesman, account, type
        Lines will only be merged if:
        * Invoice lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param keep_references: If True, keep reference of original invoices

         @return: new account invoice id

        """

        # Looks like account_id doesn not consider multi company
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'account_id'):
                    if not field_val:
                        field_val = False
                if (isinstance(field_val, browse_record) and
                        field != 'invoice_line_tax_ids' and
                        field != 'sale_line_ids'):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif (isinstance(field_val, list) or
                        field == 'invoice_line_tax_ids' or
                        field == 'sale_line_ids'):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        # compute what the new invoices should contain
        new_invoices = {}
        seen_origins = {}
        seen_client_refs = {}
        comments = False

        selected_invoices = []
        if manually_selected:
            # Make sure only passed invoices are used to merge
            selected_invoices = self.filtered(lambda x: x.state == "passed")
        else:
            selected_invoices = self._get_passed_invoices(company)

        # Does not take too long
        # Get passed invoices & prepare values from there for new invoice
        for account_invoice in selected_invoices:
            invoice_key = make_key(
                account_invoice, self._get_invoice_key_cols())
            new_invoice = new_invoices.setdefault(invoice_key, ({}, []))
            origins = seen_origins.setdefault(invoice_key, set())
            client_refs = seen_client_refs.setdefault(invoice_key, set())
            new_invoice[1].append(account_invoice.id)
            invoice_infos = new_invoice[0]
            if not invoice_infos:
                invoice_infos.update(
                    self._get_first_invoice_fields(account_invoice))
                origins.add(account_invoice.origin)
                client_refs.add(account_invoice.reference)
                if not keep_references:
                    invoice_infos.pop('name')
            else:
                if account_invoice.name and keep_references:
                    invoice_infos['name'] = \
                        (invoice_infos['name'] or '') + ' ' + \
                        account_invoice.name
                if account_invoice.origin and \
                        account_invoice.origin not in origins:
                    invoice_infos['origin'] = \
                        (invoice_infos['origin'] or '') + ' ' + \
                        account_invoice.origin
                    origins.add(account_invoice.origin)
                if account_invoice.reference \
                        and account_invoice.reference not in client_refs:
                    invoice_infos['reference'] = \
                        (invoice_infos['reference'] or '') + ' ' + \
                        account_invoice.reference
                    client_refs.add(account_invoice.reference)
                # Carry delivery partner over to merged invoice
                if account_invoice.partner_shipping_id:
                    invoice_infos["partner_shipping_id"] = account_invoice.partner_shipping_id.id

                ###Combine Comments
                if account_invoice.comment:
                    current_comment = account_invoice.comment
                    invoice_infos["comment"] = str(invoice_infos['comment']) + " " + str(current_comment)

                # Carry global discounts from single to merged invoices
                if len(account_invoice.global_discount_ids) > 0:
                    # If not yet in invoice_infos add with current global discount ids
                    if "global_discount_ids" not in invoice_infos:
                        invoice_infos["global_discount_ids"] = [(6, 0, account_invoice.global_discount_ids.ids)]
                    # Otherwise add new global discount ids
                    else:
                        current_ids = invoice_infos["global_discount_ids"][0][2]
                        invoice_infos["global_discount_ids"] = [(6, 0, list(set(current_ids + account_invoice.global_discount_ids.ids)))]

            for invoice_line in account_invoice.invoice_line_ids:
                line_key = make_key(
                    invoice_line, self._get_invoice_line_key_cols())

                o_line = invoice_infos['invoice_line_ids'].\
                    setdefault(line_key, {})

                if o_line:
                    # merge the line with an existing line
                    o_line['quantity'] += invoice_line.quantity
                    o_line['add_a_note'] = invoice_line.add_a_note
                    # Make sure CW quantities and uom's are considered
                    if invoice_line.product_id._is_cw_product():
                        o_line["product_cw_uom_qty"] += invoice_line.product_cw_uom_qty
                        o_line["product_cw_uom"] = invoice_line.product_cw_uom.id
                else:
                    # append a new "standalone" line
                    o_line['quantity'] = invoice_line.quantity
                    o_line['add_a_note'] = invoice_line.add_a_note
                    # Make sure CW quantities and uom's are considered
                    if invoice_line.product_id._is_cw_product():
                        o_line["product_cw_uom_qty"] = invoice_line.product_cw_uom_qty
                        o_line["product_cw_uom"] = invoice_line.product_cw_uom.id

        newinvoice = []
        allinvoices = []
        allnewinvoices = []
        invoices_info = {}
        old_invoices = self.env['account.invoice']
        qty_prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        # Task: Create new (merged) invoice or make single invoices identifiable for confirming & sending later
        # FIXME: Potential for optimization, consider committing data to database after each invoice created and old one cancelled
        for invoice_key, (invoice_data, old_ids) in new_invoices.items():
            # skip merges with only one invoice
            if len(old_ids) < 2:
                allinvoices += (old_ids or [])
                # If len of old_ids is one, confirm that invoice
                if len(old_ids) == 1:
                    # Make sure old invoice will be stored in newinvoice variable, since this is returned and no new invoice is created
                    newinvoice = self.env["account.invoice"].browse(old_ids)
                    # Make sure to set is_merged to true, so it's later identified when validating & sending the invoice
                    newinvoice.is_merged = True
                    newinvoice._set_global_discounts_by_tax()
                    newinvoice.compute_taxes()
                    newinvoice._compute_amount()
                continue
            # cleanup invoice line data
            for key, value in invoice_data['invoice_line_ids'].items():
                value.update(dict(key))

            if remove_empty_invoice_lines:
                invoice_data['invoice_line_ids'] = [
                    (0, 0, value) for value in
                    invoice_data['invoice_line_ids'].values() if
                    not float_is_zero(
                        value['quantity'], precision_digits=qty_prec)]
            else:
                invoice_data['invoice_line_ids'] = [
                    (0, 0, value) for value in
                    invoice_data['invoice_line_ids'].values()]

            if date_invoice:
                invoice_data['date_invoice'] = date_invoice
            
            invoice_data['is_merged'] = True
            # create the new invoice
            newinvoice = self.with_context(is_merge=True).create(invoice_data)
            
            invoices_info.update({newinvoice.id: old_ids})
            allinvoices.append(newinvoice.id)
            allnewinvoices.append(newinvoice)
            # cancel old invoices
            old_invoices = self.env['account.invoice'].browse(old_ids)
            old_invoices.with_context(is_merge=True).action_invoice_merged()
            # consider adding env.cr.commit(), after creating new & cancelling old invoice

        # Make link between original sale order
        # None if sale is not installed
        invoice_line_obj = self.env['account.invoice.line']
        for new_invoice_id in invoices_info:
            if 'sale.order' in self.env.registry:
                sale_todos = old_invoices.mapped(
                    'invoice_line_ids.sale_line_ids.order_id')
                for org_so in sale_todos:
                    for so_line in org_so.order_line:
                        invoice_line = invoice_line_obj.search(
                            [('id', 'in', so_line.invoice_lines.ids),
                             ('invoice_id', '=', new_invoice_id)])
                        if invoice_line:
                            so_line.write(
                                {'invoice_lines': [(6, 0, invoice_line.ids)]})

        # recreate link (if any) between original analytic account line
        # (invoice time sheet for example) and this new invoice
        anal_line_obj = self.env['account.analytic.line']
        if 'invoice_id' in anal_line_obj._fields:
            for new_invoice_id in invoices_info:
                anal_todos = anal_line_obj.search(
                    [('invoice_id', 'in', invoices_info[new_invoice_id])])
                anal_todos.write({'invoice_id': new_invoice_id})

        # Compute stuff for new invoice
        for new_invoice in allnewinvoices:
            new_invoice.compute_taxes()
            new_invoice._set_global_discounts_by_tax()
            new_invoice._compute_amount()
        return newinvoice
