# -*- encoding: utf-8 -*-

import ftplib
import logging
import sys

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr

PY2 = sys.version_info[0] == 2

if PY2:
    from StringIO import StringIO
else:
    from io import BytesIO as StringIO

_logger = logging.getLogger(__name__)


class SynchronizationException(Exception):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self.args = (name, value)


class FTPConnection(models.Model):

    _inherit = 'edi.connection'

    connection_type = fields.Selection(selection_add=[('ftp', 'FTP')])

    host = fields.Char()
    user = fields.Char()
    password = fields.Char()
    folder = fields.Char()
    is_active = fields.Boolean(string='Active')

    on_conflict = fields.Selection([
        ('raise', 'Raise exception'),
        ('rename', 'Rename file'),
        ('replace', 'Replace file')
    ], default='raise', required=True, string='Conflict strategy')
    on_conflict_rename_extension = fields.Char(default='old')
    on_clean_integration = fields.Selection([
        ('rename', 'Rename'),
        ('replace', 'Delete')
    ], default='rename', required=True, string='Clean strategy')
    on_clean_integration_rename_extension = fields.Char(default='bak')

    def _ftp_test(self):

        self.ensure_one()

        try:
            conn = self._connect()
            conn.quit()
        except Exception as e:
            raise UserError(_('Connection Test Failed! Here is what we got instead:\n %s') % ustr(e))
        else:
            raise UserError(_('Connection Test Succeeded! Everything seems properly set up!'))

    def _ftp_send_synchronization(self, synchronization, *args, **kwargs):
        """
        """

        self.ensure_one()

        filename = synchronization.filename or synchronization.name
        content = self._get_content(synchronization)
        self.ftp_server = None

        try:

            self.ftp_server = self._connect()

            try:
                self._check_filename(
                    filename,
                    on_conflict=self.on_conflict,
                    extension=self.on_conflict_rename_extension
                )
                self._upload_file(filename, content)
            finally:
                if self.ftp_server is not None:
                    self.ftp_server.quit()

        except Exception as e:
            params = (ustr(self.ftp_server), ustr(self.ftp_server.host), e.__class__.__name__, ustr(e))
            msg = _("Sending synchronization failed via FTP server '%s: %s'.\n%s: %s") % params

            _logger.info(msg)

            raise SynchronizationException(_("Failure to send synchronization"), msg)

    def _ftp_fetch_synchronizations(self, *args, **kwargs):
        """
        """

        self.ensure_one()

        result = []
        self.ftp_server = None

        try:
            self.ftp_server = self._connect()
            existing_filenames = getattr(self.ftp_server, 'mlst', self.ftp_server.nlst)()

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
                    params = (filename, ustr(self.ftp_server), ustr(self.ftp_server.host), e.__class__.__name__, ustr(e))
                    msg = _("Fetching file '%s' failed via FTP server '%s: %s'.\n%s: %s") % params

                    _logger.info(msg)
                else:
                    values.update({
                        'filename': filename,
                        'content': content
                    })
                    result.append(values)

        except Exception as e:
            params = (
                ustr(self.ftp_server),
                ustr(self.ftp_server.host),
                e.__class__.__name__,
                ustr(e)
            )
            msg = _("Fetching synchronizations failed via FTP server '%s: %s'.\n%s: %s") % params

            _logger.info(msg)

        finally:
            if self.ftp_server is not None:
                self.ftp_server.quit()
        return result

    def _ftp_clean_synchronization(self, filename, *args, **kwargs):
        """
        """
        self.ensure_one()
        self.ftp_server = None

        try:

            self.ftp_server = self._connect()

            try:
                self._check_filename(
                    filename,
                    on_conflict=self.on_clean_integration,
                    extension=self.on_clean_integration_rename_extension
                )
            finally:
                if self.ftp_server is not None:
                    self.ftp_server.quit()

        except Exception as e:
            params = (
                filename,
                ustr(self.ftp_server),
                e.__class__.__name__,
                ustr(e)
            )
            msg = _("Cleaning synchronization '%s' failed via FTP server '%s'.\n%s: %s") % params

            _logger.info(msg)

            raise SynchronizationException(_("Failure while cleaning synchronization"), msg)

    def _ftp_connect(self):

        self.ensure_one()

        server = ftplib.FTP(
            host=self.host,
            user=self.user,
            passwd=self.password
        )

        if self.is_active:
            server.set_pasv(False)

        if self.folder:
            server.cwd(self.folder)

        return server

    @api.model
    def _check_filename(self, filename, on_conflict='raise', extension='old'):
        if self.connection_type == 'ftp':
            existing_filenames = getattr(self.ftp_server, 'mlst', self.ftp_server.nlst)()
            conflicts = set(existing_filenames) & set([filename])

            if not conflicts:
                return

            if conflicts and on_conflict == 'rename':
                self.ftp_server.rename(filename, filename + '.' + extension)
            elif conflicts and on_conflict == 'replace':
                self.ftp_server.delete(filename)
            else:
                raise UserError(_('File \'%s\' already present if FTP server') % filename)

    @api.model
    def _download_file(self, filename):
        if self.connection_type == 'ftp':
            data = StringIO()
            self.ftp_server.retrbinary('RETR %s' % filename, data.write)
            content = data.getvalue()
            data.close()
            return content.decode()

        return super(FTPConnection, self)._download_file(filename)

    @api.model
    def _upload_file(self, filename, content):
        if self.connection_type == 'ftp':
            self.ftp_server.storbinary('STOR %s' % filename, StringIO(content.encode()))
        else:
            super(FTPConnection, self)._upload_file(filename, content)

    @api.model
    def _get_content(self, synchronization):
        return synchronization.content

    @api.model
    def _is_valid_filename(self, filename):
        if filename in ['.', '..']:
            return False

        # NOTE: ftplib does not provides a way to differentiate between normal
        #       files and folders, we expect files to have a '.' on its name,
        #       obviously that is a rather random heuristic.
        fname, _, extension = filename.rpartition('.')
        if not fname or extension in ['bak', 'old']:
            return False

        return True
