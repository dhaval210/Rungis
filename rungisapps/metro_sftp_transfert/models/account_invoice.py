import base64
from lxml import etree
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from base64 import decodebytes
import paramiko
try:
    import pysftp
except ImportError:
    raise ImportError(
        'This module needs pysftp to automatically write backups to the FTP through SFTP. Please install pysftp '
        'on your system. (sudo pip3 install pysftp)')

logger = logging.getLogger(__name__)


class My_Connection(pysftp.Connection):
    def __init__(self, *args, **kwargs):
        self._sftp_live = False
        self._transport = None
        super().__init__(*args, **kwargs)


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'base.ubl']

    # Determins if an invoice was already generated for sending it to a SFTP server
    generated_invoice = fields.Boolean('generated invoice', copy=False)
    
    @api.multi
    def generate_ubl_xml_string_transfer(self, version='2.1', invoice_ids=None, sftp=False, company=None):
        # add sftp flag to prevent the generated_invoice to be set to True before sending the invoice to SFTP
        logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        # xml_roots = etree.Element('Invoice', nsmap=nsmap)
        inv_obj = self.env['account.invoice']
        context = dict(self._context or {})
        # If invoice_ids is not given, search for invoices (the old way), otherwise use given invoices
        if not invoice_ids:
            domain = [
                ('state','in',('open','paid')),
                ('type','in',('out_invoice', 'out_refund')),
                ('generated_invoice','=',False),
            ]
            if company:
                domain.append(('company_id', '=', company.id))
            invoice_ids = inv_obj.search(domain)
        if sftp:
            for invoice in invoice_ids:
                invoice.generated_invoice = True
        xml_root = self.with_context(lang=lang).\
            generate_invoice_ubl_xml_etree_extention(search_invoice = invoice_ids,version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID ')
            #'(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string

    @api.multi
    def embed_ubl_xml_in_pdf(self, pdf_content=None, pdf_file=None, invoice=None):
        self.ensure_one()
        if (    
                self.type in ('out_invoice', 'out_refund') and
                self.state in ('open', 'paid')):
            version = self.get_ubl_version()
            ubl_filename = self.get_ubl_filename(version=version)
            xml_string = ""
            # If invoice is given generate xml for invoice
            if invoice:
                xml_string = self.generate_ubl_xml_string_transfer(version=version, invoice_ids=invoice)
            else:
                xml_string = self.generate_ubl_xml_string_transfer(version=version)
            pdf_content = self.embed_xml_in_pdf(
                xml_string, ubl_filename,
                pdf_content=pdf_content, pdf_file=pdf_file)
        return pdf_content

    @api.multi
    def auto_generate_ubl_xml_file(self, company=None):
        # If at least 1 invoice is given (function is called like invoices.auto_generate_ubl_xml_file())
        if self:
            version = self.get_ubl_version()
            xml_string = self.generate_ubl_xml_string_transfer(version=version, sftp=True, invoice_ids=self, company=company)
            filename = self.get_ubl_filename(version=version)
            ctx = {}
            attach = self.env['ir.attachment'].with_context(ctx).create({
                    'name': filename, #'{0}_{1}.xml'.format(filename,now.strftime("%Y%m%d%H%M%S")),
                    # 'res_id': self.id,
                    'res_model': str(self[0]._name),
                    'datas': base64.b64encode(xml_string),
                    'datas_fname': filename, #'{0}_{1}.xml'.format(filename,now.strftime("%Y%m%d%H%M%S")),
                    'type': 'binary',
                    'public': 'True',
                    'to_transfert': 'True'
                    })
            logger.debug('UBL XML Invoice file are generated For Today')
            return attach
        return None

    def action_invoice_sent(self):
        self.ensure_one()
        # Initiate SFTP transfer for the current invoice
        if self.partner_id and self.partner_id.transfert_mode == "SFTP":
            self.sftp_transfer_invoices(self.partner_id)
            msg = "Invoice successfully transferred to %s." % self.partner_id.sftp_host
            self.message_post(body=msg)
            self.sent = True
            return
        res = super(AccountInvoice, self).action_invoice_sent()
        # checking for is_merged should only activate that functionality for merged invoices, but no other records
        if res.get("context", False) and res.get("context").get("custom_layout", False) and self.is_merged:
            ctx = res.get("context")
            template = self.env.ref('metro_rungis_invoice_robot.mail_template_invoice', False)
            # Setting custom layout to an invalid value will stop the base template from being inserted
            # From mail/models/res_partner.py:108 _notify():
            # template_xmlid = message.layout if message.layout else 'mail.message_notification_email'
            ctx["custom_layout"] = "metro_rungis_invoice_robot.does_not_exist"
            ctx["default_template_id"] = template and template.id or "default_template_id" in ctx and ctx["default_template_id"] or False
            res["context"] = ctx
        return res

    def sftp_transfer_invoices(self, partner):
        """This function transfers the invoices, created since the last transfer, to the partner's (S)FTP server.
        Before transferring the files the function makes sure the partner is properly configured.

        Args:
            partner (res.partner): Partner the invoices should be transferred to

        Raises:
            ValidationError: If the password or Private Key of the connection is wrong
            UserError: If another unexcepted error has occured or no connection to the server could be established
        """
        cnopts = pysftp.CnOpts()

        if not partner.sftp_server.sftp_active:
            raise UserError(_("The SFTP Server %s (%d) is inactive." % (partner.sftp_server.sftp_host, partner.sftp_server.id)))
        
        # Make sure SFTP controls are existing before working with the values
        # E.g. 1st cron was executed and some user changed the configuration of the partner inbetween
        err = partner._check_valid_process_controls()[0]
        if len(err) > 0:
            logger.warn("There was an error with the contact {} ({})".format(partner.name, partner.id))
            msg = "<p>There were some errors while trying to transfer invoices for this partner via sftp:</p><ul>"
            for e in err:
                msg += "<li>" + e + "</li>"
            msg += "</ul>"
            partner.message_post(body=msg)
            return

        if partner.sftp_server.sftp_hostkeys:
            keydata = bytes(partner.sftp_server.sftp_hostkeys, 'utf-8')
            key = paramiko.RSAKey(data=decodebytes(keydata))
            cnopts.hostkeys.add(str(partner.sftp_server.sftp_host), 'ssh-rsa', key)
        else:
            cnopts.hostkeys = None

        attach_invoice = self.generate_attachment_file(partner)
        if not attach_invoice:
            attach_invoice = self.env["ir.attachment"].search([
                ("res_model", "=", "account.invoice"),
                ("res_id", "=", self.id),
            ], limit=1, order="id asc")
            
        file_name = attach_invoice.store_fname
        sftp_path = partner.sftp_server.sftp_path
        p = sftp_path if sftp_path.endswith("/") else sftp_path + "/"
        # Make sure file name of invoice does not contain /, since this would break the fs of linux and will result in a not uploaded file
        remote_path = p + attach_invoice.name.replace("/", "_")
        local_path =  attach_invoice._full_path(file_name)
        
        if not remote_path.endswith(".pdf") and attach_invoice.mimetype == "application/pdf":
            remote_path += ".pdf"

        # NOTE: Need to consider the access rights of the sftp user, if /home/sftp is the root folder for sftp user,
        # and user wants to upload to /home/sftp/uploads, path must be /uploads/, since linux will prepend the path to the sftp users root folder
        conn = None
        try: 
            if partner.sftp_server.auth_mode == "password":
                conn = My_Connection(partner.sftp_server.sftp_host, username=partner.sftp_server.sftp_user, password=partner.sftp_server.sftp_password, port=partner.sftp_server.sftp_port, cnopts=cnopts)
            elif partner.sftp_server.auth_mode == "key":
                pw = None
                if partner.sftp_server.sftp_key_pass != "":
                    pw = partner.sftp_server.sftp_key_pass
                key = paramiko.RSAKey.from_private_key_file(partner.sftp_server.sftp_private_key, password=pw)
                conn = My_Connection(partner.sftp_server.sftp_host, username=partner.sftp_server.sftp_user, private_key=key, port=partner.sftp_server.sftp_port, cnopts=cnopts)
            else:
                raise ValidationError(_("Please enter either a private key or password before testing the connection."))
            with conn as sftp:
                logger.debug('connection success')
                l = sftp.listdir()
                sftp.put(local_path, remote_path)
                logger.debug('File was sended successfully')
        except paramiko.ssh_exception.SSHException as e:
            raise UserError(_('%s.') % e)
        except paramiko.PasswordRequiredException as e:
            raise ValidationError(_("%s") % e)
        except Exception as e:
            logger.warn(e)
            raise UserError(_("%s") % e)
        finally:
            if conn:
                conn.close()

    def async_send_invoices(self, invoice):
        if invoice.partner_id.transfert_mode == 'SFTP':
            invoice.sftp_transfer_invoices(invoice.partner_id)
            invoice.sent = True
            # Post message into chatter
            msg = "Invoice successfully transferred to %s." % invoice.partner_id.sftp_server.sftp_host
            invoice.message_post(body=msg)
            self.env.cr.commit()
        else:
            super(AccountInvoice, self).async_send_invoices(invoice)
