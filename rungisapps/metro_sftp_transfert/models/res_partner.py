from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import paramiko
from base64 import decodebytes
try:
    import pysftp
except ImportError:
    raise ImportError(
       'This module needs pysftp to automatically write backups to the FTP through SFTP. Please install pysftp '
       'on your system. (sudo pip3 install pysftp)')


class My_Connection(pysftp.Connection):
    def __init__(self, *args, **kwargs):
        self._sftp_live = False
        self._transport = None
        super().__init__(*args, **kwargs)


class ResPartner(models.Model):
    _inherit = "res.partner"

    transfert_mode = fields.Selection(
        selection_add=[('SFTP', 'SFTP')],
        help=" * The Mail method will send the invoices to partners mail.\n"
             " * The Portal method will send the invoices to the portal account partner.\n"
             " * The SFTP will send the invoices to partner server.",
    )
    sftp_server = fields.Many2one(
        comodel_name="sftp.transfert",
        domain="[('sftp_active', '=', True)]",
        string="SFTP Server"
    )

    @api.one
    def _check_valid_process_controls(self):
        err = super(ResPartner, self)._check_valid_process_controls()[0]
        # Check transfer modes and make transfer mode dependent error checks
        if self.transfert_mode == "SFTP":
            if not self.sftp_server:
                err.append(_("Please set a SFTP server"))
            else:
                server = self.sftp_server
                if not server.sftp_host:
                    err.append(_("SFTP Host missing for SFTP server %s" % server.name))
                if not server.sftp_user:
                    err.append(_("SFTP User missing for SFTP server %s" % server.name))
                if not server.sftp_port:
                    err.append(_("SFTP Port missing for SFTP server %s" % server.name))
                if not server.sftp_path:
                    err.append(_("SFTP Path missing (/ must be entered at least) for SFTP server %s" % server.name))
        # Return error without trailing newline
        return err
