# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import api, fields, models


class Connection(models.Model):

    _name = 'edi.connection'
    _description = 'EDI Connection'

    name = fields.Char(required=True)
    connection_type = fields.Selection(selection=[], required=True, string='Type')
    configuration = fields.Text()

    @api.model
    def create(self, values):
        """
        """

        vals = {}
        if 'configuration' in values:
            vals = json.loads(values['configuration'])

        vals.update(values)

        return super(Connection, self).create(vals)

    @api.multi
    def test(self):
        """
        """

        self.ensure_one()
        getattr(self, '_%s_test' % self.connection_type)()

    def _connect(self):
        return getattr(self, '_%s_connect' % self.connection_type)()

    def send_synchronization(self, synchronization, *args, **kwargs):
        """
        """

        self.ensure_one()
        getattr(self, '_%s_send_synchronization' % self.connection_type)(synchronization, *args, **kwargs)

    def fetch_synchronizations(self, *args, **kwargs):
        """
        """

        self.ensure_one()
        return getattr(self, '_%s_fetch_synchronizations' % self.connection_type)(*args, **kwargs)

    def clean_synchronization(self, filename, status, *args, **kwargs):
        """
        """

        self.ensure_one()
        getattr(
            self,
            '_%s_%s_clean_synchronization' % (self.connection_type, status),
            getattr(
                self,
                '_%s_clean_synchronization' % self.connection_type,
                lambda *a, **kw: None
            )
        )(filename, *args, **kwargs)
