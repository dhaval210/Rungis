from odoo import models, fields, api, _
from base64 import decodebytes
from odoo.exceptions import UserError, ValidationError
import paramiko
try:
    import pysftp
except ImportError:
    raise ImportError(
       'This module needs pysftp to automatically write backups to the FTP through SFTP. Please install pysftp '
       'on your system. (sudo pip3 install pysftp)')
import logging
logger = logging.getLogger(__name__)

class My_Connection(pysftp.Connection):
    def __init__(self, *args, **kwargs):
        self._sftp_live = False
        self._transport = None
        super().__init__(*args, **kwargs)


class SftpTransfert(models.Model):
    _name = 'sftp.transfert'
    _rec_name = 'name'
    
    name = fields.Char(string="Server Name", required=True, help="Name of the server")
    auth_mode = fields.Selection([
        ("password", "Password"),
        ("key", "SSH Keys")
    ], default="password")
    sftp_host = fields.Char(string="Host",required=True, help="Ip Address to transfer file")
    sftp_path = fields.Char("Storage Directory Path",required=True, help="Servers Storage path to send file")
    sftp_user = fields.Char("Username" ,required=True, help="Ip Address to transfer file")
    sftp_password = fields.Char("Password",required=False, help="Ip Address to transfer file")
    sftp_private_key = fields.Char("Private Key Path", required=False, help="Private key of user to identify with that instead of the password.")
    sftp_key_pass = fields.Char("Private Key Password", required=False, help="If your private key is protected with a password please enter it here.")
    sftp_hostkeys = fields.Char("Hostkeys",required=False,help="SSH key to secure ssh sever access")
    sftp_port = fields.Integer ("Port",help="SSh Port by Default if 22",default=22)
    sftp_active = fields.Boolean('Active',default=False)
    
    # Remove unique constraint on boolean field
    _sql_constraints = [(
        'sftp_active_unique',
        'Check(1=1)',
        'An SFTP Server is already activated'
        )]
    
    @api.model
    def create(self, vals):
        if not vals["sftp_password"] and not vals["sftp_private_key"]:
            raise ValidationError(_("Please enter either a password or a private key."))
        return super(SftpTransfert, self).create(vals)
    
    @api.multi
    def write(self, vals):
        res = super(SftpTransfert, self).write(vals)
        for r in self:
            if not r.sftp_password and not r.sftp_private_key:
                raise ValidationError(_("Please enter either a password or a private key."))
        return res

    def sftp_test_connection(self):
        cnopts = pysftp.CnOpts()
        
        if self.sftp_hostkeys:
            keydata = bytes(self.sftp_hostkeys, 'utf-8')
            key = paramiko.RSAKey(data=decodebytes(keydata))
            cnopts.hostkeys.add(str(self.sftp_host), 'ssh-rsa', key)
        else:
            cnopts.hostkeys = None

        try:
            conn = None
            if self.auth_mode == "password":
                conn = My_Connection(self.sftp_host, username=self.sftp_user, password=self.sftp_password, port=self.sftp_port, cnopts=cnopts)
            elif self.auth_mode == "key":
                pw = None
                if self.sftp_key_pass != "":
                    pw = self.sftp_key_pass
                key = paramiko.RSAKey.from_private_key_file(self.sftp_private_key, password=pw)
                conn = My_Connection(self.sftp_host, username=self.sftp_user, private_key=key, port=self.sftp_port, cnopts=cnopts)
            else:
                raise ValidationError(_("Please enter either a private key or password before testing the connection."))
            with conn as sftp:
                raise UserError(('connection success'))
        except paramiko.ssh_exception.SSHException as e:
            raise UserError(_('%s.') % e)
        except paramiko.PasswordRequiredException as e:
            raise ValidationError(_("%s") % e)
        except Exception as e:
            raise UserError(_("%s") % e)

    def sftp_transfer_file(self, host_ids=[]):
        """This function transfers all invoices generated since the last time bundled as an XML to a host given as an argument.
        It's currently used inside the Transfer Invoices cron job


        Args:
            host_ids (list<int>): The IDs of the sftp.transfert records the UBL invoices should be transferred to. Defaults to [], if no ids are given the function will quit w/o any errors.

        Raises:
            ValidationError: Thrown when password or key is wrong
            UserError: Thrown when the connection fails or an unexpected error occurs.
        """
        if len(host_ids) < 1:
            return
        sftp_obj = self.env["sftp.transfert"].browse(host_ids)
        for rec in sftp_obj:
            cnopts = pysftp.CnOpts()

            if self.sftp_hostkeys:
                keydata = bytes(rec.sftp_hostkeys, 'utf-8')
                key = paramiko.RSAKey(data=decodebytes(keydata))
                cnopts.hostkeys.add(str(rec.sftp_host), 'ssh-rsa', key)
            else:
                cnopts.hostkeys = None

            # NOTE: Make sure the invoices are generated bundled and will be sent as one XML file!!!! -> should be done
            companies = self.env["res.company"].search([
                ("run_invoice_robot", "=", True),
            ])
            for company in companies:
                # find invoices and credit notes which were not sent to sftp yet
                invoices = self.env["account.invoice"].search([
                    ("generated_invoice", "=", False),
                    ('state','in',('paid','open')),
                    ('type','in',('out_invoice', 'out_refund')),
                    ("company_id", "=", company.id)
                ])
                # generate attachment based on found invoices
                attach_id = invoices.auto_generate_ubl_xml_file(company)
                if attach_id:
                    file_name = attach_id.store_fname
                    attach_id.to_transfert = False
                    attach_id.data_to_transfert = False

                    # Make sure name does not contain / (which is used as separator in linux filesystem)
                    rp = rec.sftp_path if rec.sftp_path.endswith("/") else rec.sftp_path + "/"
                    remote_path = rp + attach_id.name.replace("/", "_")
                    local_path =  attach_id._full_path(file_name)
                    # upload file
                    try:
                        conn = None
                        if rec.auth_mode == "password":
                            conn = My_Connection(rec.sftp_host, username=rec.sftp_user, password=rec.sftp_password, port=rec.sftp_port, cnopts=cnopts)
                        elif rec.auth_mode == "key":
                            pw = None
                            if rec.sftp_key_pass != "":
                                pw = rec.sftp_key_pass
                            key = paramiko.RSAKey.from_private_key_file(rec.sftp_private_key, password=pw)
                            conn = My_Connection(rec.sftp_host, username=rec.sftp_user, private_key=key, port=rec.sftp_port, cnopts=cnopts)
                        else:
                            raise ValidationError(_("Please enter either a private key or password before testing the connection."))
                        with conn as sftp:
                            logger.debug('connection success')
                            l = sftp.listdir()
                            sftp.put(local_path, remote_path)
                            logger.debug('File was sended successefully')
                    except paramiko.ssh_exception.SSHException as e:
                        raise UserError(_('%s.') % e)
                    except paramiko.PasswordRequiredException as e:
                        raise ValidationError(_("%s") % e)
                    except Exception as e:
                        raise UserError(_("%s") % e)
