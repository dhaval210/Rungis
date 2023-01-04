# -*- encoding: utf-8 -*-

import logging
import sys

import paramiko
import socket

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr

from odoo.addons.edi_ftp_connection.models.ftp_connection import SynchronizationException

PY2 = sys.version_info[0] == 2

if PY2:
    from StringIO import StringIO
else:
    from io import BytesIO as StringIO

_logger = logging.getLogger(__name__)


class SFTPConnection(models.Model):

    _inherit = 'edi.connection'

    connection_type = fields.Selection(selection_add=[('sftp', 'SFTP')])

    def _sftp_test(self):

        self.ensure_one()

        try:
            connection = self._connect()
            connection.close()

        except Exception as e:
            raise UserError(_('Connection Test Failed! Here is what we got instead:\n %s') % ustr(e))

        else:
            raise UserError(_('Connection Test Succeeded! Everything seems properly set up!'))

    def _sftp_send_synchronization(self, synchronization, *args, **kwargs):
        """
        """
        self.ensure_one()

        filename = synchronization.filename or synchronization.name
        content = self._get_content(synchronization)
        self.sftp_server = None

        try:
            self.sftp_server = self._connect()
            try:
                self._check_filename(
                    filename,
                    on_conflict=self.on_conflict,
                    extension=self.on_conflict_rename_extension
                )
                self._upload_file(filename, content)
            finally:
                if self.sftp_server is not None:
                    self.sftp_server.close()

        except Exception as e:
            params = (ustr(self.host), e.__class__.__name__, ustr(e))
            msg = _("Sending synchronization failed via SFTP server 'Paramiko - SFTPClient : %s'.\n%s: %s") % params

            _logger.info(msg)

            raise SynchronizationException(_("Failure to send synchronization"), msg)

    def _sftp_fetch_synchronizations(self, *args, **kwargs):
        """
        """

        self.ensure_one()

        result = []
        self.sftp_server = None

        try:
            self.sftp_server = self._connect()
            existing_filenames = self.sftp_server.listdir()

            filenames = []
            for fname in existing_filenames:
                if not self._is_valid_filename(fname):
                    continue
                filenames.append(fname)

            for filename in filenames:
                values = {
                    'filename': False,
                    'content': False
                }
                try:
                    content = self._download_file(filename)
                except Exception as e:
                    params = (filename, ustr(self.host), e.__class__.__name__, ustr(e))
                    msg = _("Fetching file '%s' failed via SFTP server 'Paramiko - SFTPClient : %s'.\n%s: %s") % params

                    _logger.info(msg)
                else:
                    values.update({
                        'filename': filename,
                        'content': content
                    })
                    result.append(values)

        except Exception as e:
            params = (
                # ustr(self.sftp_server.__class__),
                ustr(self.host),
                e.__class__.__name__,
                ustr(e)
            )
            msg = _("Fetching synchronizations failed via SFTP server 'Paramiko - SFTPClient : %s'.\n%s: %s") % params

            _logger.info(msg)

        finally:
            if self.sftp_server is not None:
                self.sftp_server.close()
        return result

    def _sftp_clean_synchronization(self, filename, *args, **kwargs):
        """
        """
        self.ensure_one()
        self.sftp_server = None

        try:
            self.sftp_server = self._connect()

            try:
                self._check_filename(
                    filename,
                    on_conflict=self.on_clean_integration,
                    extension=self.on_clean_integration_rename_extension
                )
            finally:
                if self.sftp_server is not None:
                    self.sftp_server.close()

        except Exception as e:
            params = (
                filename,
                e.__class__.__name__,
                ustr(e)
            )
            msg = _("Cleaning synchronization '%s' failed via SFTP server 'Paramiko - SFTPClient'.\n%s: %s") % params

            _logger.info(msg)

            raise SynchronizationException(_("Failure while cleaning synchronization"), msg)

    def _sftp_connect(self):

        self.ensure_one()

        transport = paramiko.Transport(self.host)
        transport.connect(
            username=self.user,
            password=self.password,
            gss_host=socket.getfqdn(self.host),
            gss_auth=False,
            gss_kex=False,
        )
        sftp = paramiko.SFTPClient.from_transport(transport)

        if self.folder:
            sftp.chdir(self.folder)

        return sftp

    @api.model
    def _check_filename(self, filename, on_conflict='raise', extension='old'):
        if self.connection_type == 'sftp':
            existing_filenames = self.sftp_server.listdir()
            conflicts = set(existing_filenames) & set([filename])

            if not conflicts:
                return

            if conflicts and on_conflict == 'rename':
                self.sftp_server.rename(filename, (filename + '.' + extension))
            elif conflicts and on_conflict == 'replace':
                self.sftp_server.remove(filename)
            else:
                raise UserError(_('File \'%s\' already present in SFTP server') % filename)

    @api.model
    def _download_file(self, filename):
        if self.connection_type == 'sftp':
            data = StringIO()
            self.sftp_server.getfo(filename, data)
            content = data.getvalue()
            data.close()
            return content.decode()

        return super(SFTPConnection, self)._download_file(filename)

    @api.model
    def _upload_file(self, filename, content):
        if self.connection_type == 'sftp':
            self.sftp_server.putfo(StringIO(content.encode('utf-8')), filename)
        else:
            super(FTPConnection, self)._upload_file(filename, content)

    @api.model
    def _get_content(self, synchronization):
        return synchronization.content

    @api.model
    def _is_valid_filename(self, filename):
        if filename in ['.', '..']:
            return False

        fname, _, extension = filename.rpartition('.')
        if not fname or extension in ['bak', 'old']:
            return False

        return True
