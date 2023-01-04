import logging
import xmlrpc.client

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class DB2SaleOrder(models.Model):
    _name = 'db2.sale.order'
    _inherit = 'db2.binding'
    _description = 'DB2 Sale Order'
    _inherits = {'sale.order': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'    
    )
    db2_order_line_ids = fields.One2many(
        comodel_name='db2.sale.order.line',
        inverse_name='db2_order_id',
        string='DB2 Order Lines'
    )
    db2_order_id = fields.Integer(
        string='DB2 Order ID',
        help="'order_id' field in DB2"
    )

    @job(default_channel='root.db2')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from DB2 """
        _super = super(DB2SaleOrder, self)
        return _super.import_batch(backend, filters=filters)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    db2_bind_ids = fields.One2many(
        comodel_name='db2.sale.order',
        inverse_name='odoo_id',
        string="DB2 Bindings",
    )

class DB2SaleOrderLine(models.Model):
    _name = 'db2.sale.order.line'
    _inherit = 'db2.binding'
    _description = 'DB2 Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    db2_order_id = fields.Many2one(
        comodel_name='db2.sale.order',
        string='DB2 Sale Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order Line',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        related='db2_order_id.backend_id',
        string='DB2 Backend',
        readonly=True,
        store=True,
        # override 'db2.binding', can't be INSERTed if True:
        required=False,
    )
    client_order_ref = fields.Char(related="order_id.client_order_ref")
    


    @api.model
    def create(self, vals):
        db2_order_id = vals['db2_order_id']
        binding = self.env['db2.sale.order'].browse(db2_order_id)
        vals['order_id'] = binding.odoo_id.id
        line_binding = self.search([
            ('external_id', '=', vals['external_id']),
            ('order_id', '=', vals['order_id']),
        ])
        if line_binding and line_binding.odoo_id and line_binding.odoo_id.id is not False:
            super(DB2SaleOrderLine, self).write(vals)
            binding = self
        else:    
            binding = super(DB2SaleOrderLine, self).create(vals)
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    db2_bind_ids = fields.One2many(
        comodel_name='db2.sale.order.line',
        inverse_name='odoo_id',
        string="DB2 Bindings",
    )

    demand_qty = fields.Float(string='Softm Demand Qty')

    @api.model
    def create(self, vals):
        old_line_id = None
        if self.env.context.get('__copy_from_quotation'):
            # when we are copying a sale.order from a canceled one,
            # the id of the copied line is inserted in the vals
            # in `copy_data`.
            old_line_id = vals.pop('__copy_from_line_id', None)
        new_line = super(SaleOrderLine, self).create(vals)
        if old_line_id:
            # link binding of the canceled order lines to the new order
            # lines, happens when we are using the 'New Copy of
            # Quotation' button on a canceled sales order
            binding_model = self.env['db2.sale.order.line']
            bindings = binding_model.search([('odoo_id', '=', old_line_id)])
            if bindings:
                bindings.write({'odoo_id': new_line.id})
        return new_line

    @api.multi
    def copy_data(self, default=None):
        data = super(SaleOrderLine, self).copy_data(default=default)[0]
        if self.env.context.get('__copy_from_quotation'):
            # copy_data is called by `copy` of the sale.order which
            # builds a dict for the full new sale order, so we lose the
            # association between the old and the new line.
            # Keep a trace of the old id in the vals that will be passed
            # to `create`, from there, we'll be able to update the
            # DB2 bindings, modifying the relation from the old to
            # the new line.
            data['__copy_from_line_id'] = self.id
        return [data]


class SaleOrderAdapter(Component):
    _name = 'db2.sale.order.adapter'
    _inherit = 'db2.adapter'
    _apply_on = 'db2.sale.order'

    _db2_table = 'S10C38BR.RUNTFILE.IODAUP'
    _db2_id = 'OAUSATZNR'
    _db2_status = 'OAUSTAT'

    def get_table_name(self):
        if len(self.backend_record.sale_order_table) > 0:
            return self.backend_record.sale_order_table
        else:
            return self._db2_table        

    def _call(self, method, arguments):
        try:
            return super(SaleOrderAdapter, self)._call(method, arguments)
        except xmlrpc.client.Fault as err:
            # this is the error in the DB2 API
            # when the sales order does not exist
            if err.faultCode == 100:
                raise IDMissingInBackend
            else:
                raise

    def search(self, filters=None, from_date=None, to_date=None):
        """ Search records according to some criteria
        and returns a list of ids
        :rtype: list
        """
        if filters is None:
            filters = {}
        dt_fmt = 'Y-m-d'
        if from_date is not None:
            filters.setdefault('created_at', {})
            filters['created_at']['from'] = '2021-01-01'
        if to_date is not None:
            filters.setdefault('created_at', {})
            filters['created_at']['to'] = '2021-10-01'
        filters['table'] = self.get_table_name()

        arguments = filters
        return super(SaleOrderAdapter, self).search(arguments)

    def read(self, external_id, filters={}):
        """ Returns the information of a record
        :rtype: dict
        """
        filters['table'] = self.get_table_name()      
        return super(SaleOrderAdapter, self).read(
            external_id, filters=filters)
