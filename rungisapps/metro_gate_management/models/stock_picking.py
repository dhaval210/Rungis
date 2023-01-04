from odoo import models, fields, api
import datetime
import re
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from odoo.tools import frozendict, lazy_classproperty, lazy_property, ormcache, \
                   Collector, LastOrderedSet, OrderedSet, pycompat, groupby
from odoo.tools.translate import _                   

regex_field_agg = re.compile(r'(\w+)(?::(\w+)(?:\((\w+)\))?)?')
VALID_AGGREGATE_FUNCTIONS = {
    'array_agg', 'count', 'count_distinct',
    'bool_and', 'bool_or', 'max', 'min', 'avg', 'sum',
}


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    gate_id = fields.Many2one(
        'stock.gate',
        group_expand='_read_group_gate_ids',
    )

    @api.model
    def create(self, vals):
        print(vals)
        res = super().create(vals)
        if res.picking_type_id.code == 'incoming':
            res.gate_id = self.env.ref('metro_gate_management.stock_gate_gr_without_gate').id
        return res

    gate_assigned = fields.Datetime(
        help='Date when gate was assigned to stock.picking'
    )

    status_complete = fields.Datetime(
        help='Date when status changes to complete'
    )

    @api.onchange('gate_id')
    def _onchange_gate_id(self):
        pickings = self.env["stock.picking"].search([
                        ("gate_id", "=", self.gate_id.id),
                        ("state", "!=", "done")])
        # Check if the gate number is alleady assigned to a stock.picking
        # record else save date to stock.picking record
        if self.gate_id.id is not False:
            if len(pickings):
                if not self.gate_id.id == self.env.ref('metro_gate_management.stock_gate_gr_without_gate').id:
                    raise ValidationError('Gate is already occupied')
            else:
                self.gate_assigned = datetime.datetime.now()
        return

    @api.onchange('state')
    def _onchange_state(self):
        # Set write_date when status changes to done
        if self.state == 'done':
            self.status_complete = datetime.datetime.now()

    # Show Gates in Kanban View even if empty
    @api.model
    def _read_group_gate_ids(self, stages, domain, order):
        gate_ids = self.env['stock.gate'].search([])
        return gate_ids

    @api.model
    def _read_group_raw(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        self.check_access_rights('read')
        groupby = [groupby] if isinstance(groupby, pycompat.string_types) else list(OrderedSet(groupby))
        groupby_list = groupby[:1] if lazy else groupby
        if self.env.context.get('gate_management_filter', False):
            if self.env["ir.config_parameter"].get_param('operation_type') is False:
                operation_type = 'Receipts'
            else:
                operation_type = self.env["ir.config_parameter"].get_param('operation_type')
            if groupby_list[0] == 'gate_id':
                domain.insert(0, '|')
                domain += [('gate_id', '!=', False)]
                domain.append(('state', 'in', ('assigned', 'partially_available')))
                domain.append(('picking_type_id', '=', operation_type))
        query = self._where_calc(domain)
        fields = fields or [f.name for f in self._fields.values() if f.store]

        annotated_groupbys = [self._read_group_process_groupby(gb, query) for gb in groupby_list]
        groupby_fields = [g['field'] for g in annotated_groupbys]
        order = orderby or ','.join([g for g in groupby_list])
        groupby_dict = {gb['groupby']: gb for gb in annotated_groupbys}

        self._apply_ir_rules(query, 'read')
        for gb in groupby_fields:
            assert gb in self._fields, "Unknown field %r in 'groupby'" % gb
            gb_field = self._fields[gb].base_field
            assert gb_field.store and gb_field.column_type, "Fields in 'groupby' must be regular database-persisted fields (no function or related fields), or function fields with store=True"

        aggregated_fields = []
        select_terms = []

        for fspec in fields:
            if fspec == 'sequence':
                continue

            match = regex_field_agg.match(fspec)
            if not match:
                raise UserError(_("Invalid field specification %r.") % fspec)

            name, func, fname = match.groups()
            if func:
                # we have either 'name:func' or 'name:func(fname)'
                fname = fname or name
                field = self._fields[fname]
                if not (field.base_field.store and field.base_field.column_type):
                    raise UserError(_("Cannot aggregate field %r.") % fname)
                if func not in VALID_AGGREGATE_FUNCTIONS:
                    raise UserError(_("Invalid aggregation function %r.") % func)
            else:
                # we have 'name', retrieve the aggregator on the field
                field = self._fields.get(name)
                if not (field and field.base_field.store and
                        field.base_field.column_type and field.group_operator):
                    continue
                func, fname = field.group_operator, name

            if fname in groupby_fields:
                continue
            if name in aggregated_fields:
                raise UserError(_("Output name %r is used twice.") % name)
            aggregated_fields.append(name)

            expr = self._inherits_join_calc(self._table, fname, query)
            if func.lower() == 'count_distinct':
                term = 'COUNT(DISTINCT %s) AS "%s"' % (expr, name)
            else:
                term = '%s(%s) AS "%s"' % (func, expr, name)
            select_terms.append(term)

        for gb in annotated_groupbys:
            select_terms.append('%s as "%s" ' % (gb['qualified_field'], gb['groupby']))

        groupby_terms, orderby_terms = self._read_group_prepare(order, aggregated_fields, annotated_groupbys, query)
        from_clause, where_clause, where_clause_params = query.get_sql()
        if lazy and (len(groupby_fields) >= 2 or not self._context.get('group_by_no_leaf')):
            count_field = groupby_fields[0] if len(groupby_fields) >= 1 else '_'
        else:
            count_field = '_'
        count_field += '_count'

        prefix_terms = lambda prefix, terms: (prefix + " " + ",".join(terms)) if terms else ''
        prefix_term = lambda prefix, term: ('%s %s' % (prefix, term)) if term else ''

        query = """
            SELECT min("%(table)s".id) AS id, count("%(table)s".id) AS "%(count_field)s" %(extra_fields)s
            FROM %(from)s
            %(where)s
            %(groupby)s
            %(orderby)s
            %(limit)s
            %(offset)s
        """ % {
            'table': self._table,
            'count_field': count_field,
            'extra_fields': prefix_terms(',', select_terms),
            'from': from_clause,
            'where': prefix_term('WHERE', where_clause),
            'groupby': prefix_terms('GROUP BY', groupby_terms),
            'orderby': prefix_terms('ORDER BY', orderby_terms),
            'limit': prefix_term('LIMIT', int(limit) if limit else None),
            'offset': prefix_term('OFFSET', int(offset) if limit else None),
        }
        self._cr.execute(query, where_clause_params)
        fetched_data = self._cr.dictfetchall()

        if not groupby_fields:
            return fetched_data

        self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)

        data = [{k: self._read_group_prepare_data(k, v, groupby_dict) for k, v in r.items()} for r in fetched_data]

        if self.env.context.get('fill_temporal') and data:
            data = self._read_group_fill_temporal(data, groupby, aggregated_fields,
                                                  annotated_groupbys)

        result = [self._read_group_format_result(d, annotated_groupbys, groupby, domain) for d in data]

        if lazy:
            # Right now, read_group only fill results in lazy mode (by default).
            # If you need to have the empty groups in 'eager' mode, then the
            # method _read_group_fill_results need to be completely reimplemented
            # in a sane way 
            result = self._read_group_fill_results(
                domain, groupby_fields[0], groupby[len(annotated_groupbys):],
                aggregated_fields, count_field, result, read_group_order=order,
            )
        return result

    def search(self, args, offset=0, limit=None, order=None, count=False):

        if self.env.context.get('gate_management_filter', False):
            if self.env["ir.config_parameter"].get_param('operation_type') is False:
                operation_type = 'Receipts'
            else:
                operation_type = self.env["ir.config_parameter"].get_param('operation_type')

            args.append(('state', 'in', ('assigned', 'partially_available')))
            args.append(('picking_type_id', '=', operation_type))

        return super(StockPicking, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count
        )

    @api.multi
    def write(self, vals):
        # gate id changed?
        if 'gate_id' in vals:
            batch_ids = []
            for picking in self:
                # moved to another gate
                if vals.get('gate_id'):
                    gate = self.env['stock.gate'].browse(vals.get('gate_id'))
                    # Check if Gate is Free
                    if gate.state is False:
                        # Has gate_id ?
                        if picking.gate_id:
                            # Set current Gate to false
                            picking.gate_id.state = False
                        # Set new Gate to True
                        gate.state = True
                        # Is Picking part of batch?
                        if picking.batch_id:
                            # Set gate id from batch
                            picking.batch_id.gate_id = vals.get('gate_id')
                            # Get all Pickings
                            batch_ids.append(picking.batch_id.id)
                    else:
                        # Error: Gate is already occupied
                        if self.env.ref('metro_gate_management.stock_gate_gr_without_gate').id != vals.get('gate_id'):
                            raise ValidationError('Tor bereits belegt')
                # moved to buffer
                else:
                    # Set current Gate to false
                    picking.gate_id.state = False
                    # Move all pickings to false
                    if picking.batch_id:
                        # Set gate id from batch
                        picking.batch_id.gate_id = vals.get('gate_id')
                        # Get all Pickings
                        batch_ids.append(picking.batch_id.id)
            if len(batch_ids):
                self = self.search([('batch_id', 'in', batch_ids)])
        return super(StockPicking, self).write(vals)

    @api.multi
    def action_cancel(self):
        for pick in self:
            if pick.gate_id:
                pick.gate_id.state = False
            return super(StockPicking, self).action_cancel()

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if self.gate_id:
            self.gate_id.state = False
        return super(StockPicking, self).button_validate()
