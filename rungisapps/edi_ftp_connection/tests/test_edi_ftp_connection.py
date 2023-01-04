# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ftplib
import json
import sys

from datetime import datetime as dt

from odoo.addons.edi_ftp_connection.models.ftp_connection import SynchronizationException
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger

PY2 = sys.version_info[0] == 2

if PY2:
    from StringIO import StringIO
else:
    from io import BytesIO as StringIO


HOST = 'api3.odoo.com'
USER = 'odoo'
PASSWORD = 'OdooAPI32018'


class ConnectionTest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(ConnectionTest, cls).setUpClass()

        cls.ftp = ftplib.FTP(host=HOST, user=USER, passwd=PASSWORD)

    @classmethod
    def tearDownClass(cls):
        super(ConnectionTest, cls).tearDownClass()

        if cls.ftp:
            cls.ftp.quit()

    def setUp(self):

        super(ConnectionTest, self).setUp()

        now = dt.utcnow()

        self.partner_model_id = self.env.ref('base.model_res_partner')

        self.out_connection = self.env['edi.connection'].create({
            'name': 'API3 FTP Connection',
            'connection_type': 'ftp',
            'configuration': json.dumps({
                'host': HOST,
                'user': USER,
                'password': PASSWORD,
                'folder': 'ftp/out',
                'on_conflict': 'rename'
            })
        })

        self.in_connection = self.env['edi.connection'].create({
            'name': 'API3 FTP Connection',
            'connection_type': 'ftp',
            'configuration': json.dumps({
                'host': HOST,
                'user': USER,
                'password': PASSWORD,
                'folder': 'ftp/in'
            })
        })

        self.out_integration = self.env['edi.integration'].create({
            'name': 'Test Outgoing Integration 1',
            'integration_type': 'out',
            'connection_id': self.out_connection.id,
            'res_model_id': self.partner_model_id.id,
            'provider_name': 'Test Partner'
        })

        self.synchronization = self.env['edi.synchronization'].create({
            'name': '%s_%s_%s_integration_%s_synchronization.txt' % (
                'out',
                self.partner_model_id.id,
                now.strftime('%s'),
                self.out_integration.id
            ),
            'integration_id': self.out_integration.id,
            'synchronization_type': 'out',
            'content': 'Hello world!'
        })

    def _clean_ftp(self, folder=None):
        """
        """

        pwd = self.ftp.pwd()

        if not folder:
            folder = '.'

        self.ftp.cwd(folder)

        filenames = self.ftp.nlst()
        for filename in filenames:
            self.ftp.delete(filename)

        self.ftp.cwd(pwd)

    def test_connect_fail(self):
        """
        """

        connection = self.env['edi.connection'].create({
            'name': 'Test FTP Connection',
            'connection_type': 'ftp',
            'configuration': json.dumps({
                'host': 'test.odoo.com',
                'user': 'odoo',
                'password': 'odoo'
            })
        })

        with self.assertRaises(UserError) as cm:
            connection.test()

        exc = cm.exception

        self.assertTrue('Connection Test Failed!' in exc.name)

    def test_connect_success(self):
        with self.assertRaises(UserError) as cm:
            self.out_connection.test()

        exc = cm.exception

        self.assertTrue('Connection Test Succeeded!' in exc.name)

    @mute_logger('odoo.addons.edi_ftp_connection.models.ftp_connection')
    def test_send_synchronization(self):
        """
        """

        self._clean_ftp('ftp/out')
        self.ftp.cwd('ftp/out')

        # First send: file doesn\'t exist on FTP server
        self.out_connection.send_synchronization(self.synchronization)

        filenames = self.ftp.nlst()

        self.assertEqual(len(filenames), 1)
        self.assertEqual(filenames[0], self.synchronization.name)

        # Second send: file already exists on FTP server -> rename
        self.out_connection.send_synchronization(self.synchronization)

        filenames = self.ftp.nlst()

        self.assertEqual(len(filenames), 2)
        self.assertTrue(self.synchronization.name in filenames)
        self.assertTrue(self.synchronization.name + '.old' in filenames)

        # Third send: file already exists on FTP server -> replace
        self.out_connection.on_conflict = 'replace'
        self.synchronization.content = 'Replaced hello world!'
        self.out_connection.send_synchronization(self.synchronization)

        filenames = self.ftp.nlst()

        self.assertEqual(len(filenames), 2)
        self.assertTrue(self.synchronization.name in filenames)
        self.assertTrue(self.synchronization.name + '.old' in filenames)

        data = StringIO()
        self.ftp.retrbinary('RETR %s' % self.synchronization.name, data.write)
        content = data.getvalue().decode()
        data.close()

        self.assertEqual(content, self.synchronization.content)

        # Fourth send: file already exists on FTP server -> raise
        self.out_connection.on_conflict = 'raise'
        with self.assertRaises(SynchronizationException) as cm:
            self.out_connection.send_synchronization(self.synchronization)

        exc = cm.exception

        self.assertTrue('File \'%s\' already present if FTP server' % self.synchronization.name in exc.value)

        self.ftp.cwd('../..')
        self._clean_ftp('ftp/out')

    @mute_logger('odoo.addons.edi_ftp_connection.models.ftp_connection')
    def test_fetch_synchronizations(self):
        """
        """

        self._clean_ftp('ftp/in')
        self.ftp.cwd('ftp/in')

        self.ftp.storbinary('STOR %s' % 'test_file.txt', StringIO(b'Hello world!'))
        self.ftp.storbinary('STOR %s' % 'test_file.txt.old', StringIO(b'Hello old world!'))

        result = self.in_connection.fetch_synchronizations()

        self.assertEqual(len(result), 1)
        result = result[0]
        self.assertTrue('test_file.txt' in result['filename'])
        self.assertEqual(result['content'], 'Hello world!')

        self.ftp.cwd('../..')
        self._clean_ftp('ftp/in')
