import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from ..components.mapper import normalize_datetime
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob


class SaleOrderImporter(Component):
    _name = 'db2.sale.order.importer'
    _inherit = 'db2.importer'
    _apply_on = 'db2.sale.order'

    def __init__(self, work_context):
        super().__init__(work_context)
        self.delete_header = False
        self.header_id = False
        self.delete_line = False
        self.line_id = False

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.
        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).
        If it returns None, the import will continue normally.
        :returns: None | str | unicode
        """

        # if self.binder.to_internal(self.external_id):
        #     return _('Already imported')

    def _clean_db2_items(self, resource):
        resource.update({
            'child': [resource]
        })
        self.delete_header = False
        self.delete_line = False
        self.external_id = resource['OAUAUFN']
        if 'X' in resource['OAUKLOKZ']:
            self.delete_header = True
            self.header_id = resource['OAUAUFN']
        if 'X' in resource['OAUPLOKZ']:
            self.delete_line = True
            self.line_id = resource['OAUAUPO']

        return resource

    def _merge_sub_items(self, product_type, top_item, child_items):
        return top_item

    def _unlink(self, binding):
        try:
            if self.delete_header is True:
                binding.odoo_id.unlink()
                binding.unlink()
                self.env.cr.commit()
            elif self.delete_line is True:
                binding_model = self.env['db2.sale.order.line']
                bindings = binding_model.search([
                    ('external_id', '=', self.external_id + '-' + self.line_id),
                ])
                if bindings.id is not False and bindings.odoo_id.id is not False:
                    bindings.odoo_id.unlink()
                    bindings.unlink()
                    self.env.cr.commit()
        except Exception as e:
            raise Exception(e)

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()
        return binding

    def _after_import_delete(self):
        # set success with self.origin_external_id
        try:
            data = {
                'OAUSTAT': '1'
            }
            self.backend_adapter.write(self.origin_external_id, data)
        except Exception as e:
            raise Exception(e)
        return

    def _after_import(self, binding):
        # set success with self.origin_external_id
        try:
            ext_id = self.db2_record['OAUAUFN'] + '-' + self.db2_record['OAUAUPO']
            pos = binding.db2_order_line_ids.filtered(lambda x: x.external_id == ext_id)
            data = {
                'OAUSTAT': '1',
                'OAUODIDK': binding.odoo_id.id, # KOPF
                'OAUODIDP': pos.odoo_id.id, # POSITION
            }
            self.backend_adapter.write(self.origin_external_id, data)
        except Exception as e:
            raise Exception(e)
        return

    def _after_import_error(self, binding, error):
        # set success with self.origin_external_id
        try:
            if isinstance(error, object) and hasattr(error, 'name'):
                error = error.name
            else:
                error = str(error)
            data = {
                'OAUSTAT': '9',
                'OAUERRT': error[:200], # max char count of 200 for as400
            }
            self.backend_adapter.write(self.origin_external_id, data)
        except Exception as e:
            raise Exception(e)
        return

    def _get_db2_data(self):
        """ Return the raw Magento data for ``self.external_id`` """
        record = super(SaleOrderImporter, self)._get_db2_data()
        if len(record) > 0:
            record = self._clean_db2_items(record[0])
            return record
        return {}

    def _check_special_fields(self):
        assert self.partner_id, (
            "self.partner_id should have been defined "
            "in SaleOrderImporter._import_addresses")
        assert self.partner_invoice_id, (
            "self.partner_id should have been "
            "defined in SaleOrderImporter._import_addresses")
        assert self.partner_shipping_id, (
            "self.partner_id should have been defined "
            "in SaleOrderImporter._import_addresses")

    def _create_data(self, map_record, **kwargs):
        return super(SaleOrderImporter, self)._create_data(
            map_record,
            **kwargs)

    def _update_data(self, map_record, **kwargs):
        return super(SaleOrderImporter, self)._update_data(
            map_record,
            **kwargs)

    def _import_dependencies(self):
        record = self.db2_record

    def _must_delete(self):
        if self.delete_header is True or self.delete_line is True:
            return True
        return False

    def run(self, external_id, force=False, data=None):
        """ Run the synchronization
        :param external_id: identifier of the record on db2
        """
        self.origin_external_id = external_id
        self.external_id = external_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.work.model_name,
            external_id,
        )

        if data:
            self.db2_record = data
            self.db2_record = self._clean_db2_items(self.db2_record)
        else:
            try:
                self.db2_record = self._get_db2_data()
            except IDMissingInBackend:
                return _('Record does no longer exist in DB2')

        skip = self._must_skip()
        if len(self.db2_record) == 0:
            raise Exception(_('could not read data for OAUSATZNR: %s in DB2. retry on next run') % external_id)
        if skip:
            return skip

        binding = self._get_binding()

        delete = self._must_delete()
        if delete:
            try:
                self._unlink(binding)
                self._after_import_delete()
            except Exception as e:
                raise Exception(e)
            return delete

        # if not force and self._is_uptodate(binding):
        #     return _('Already up-to-date.')

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the informations
        # will be updated into Odoo
        self.advisory_lock_or_retry(lock_name)
        self._before_import()

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()

        try:
            if binding:
                record = self._update_data(map_record)
                self._update(binding, record)
            else:
                record = self._create_data(map_record)
                binding = self._create(record)
            self.binder.bind(self.external_id, binding)

            self._after_import(binding)
        except Exception as e:
            self.env.cr.commit()
            self._after_import_error(binding, e)
            raise Exception(e)
