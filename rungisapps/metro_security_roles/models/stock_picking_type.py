from odoo import api, fields, models, SUPERUSER_ID


class PackageLevel(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def _apply_ir_rules(self, query, mode='read'):
        """Add what's missing in ``query`` to implement all appropriate ir.rules
          (using the ``model_name``'s rules or the current model's rules if ``model_name`` is None)

           :param query: the current query object
        """
        if self._uid == SUPERUSER_ID:
            return

        if self.env.context.get('allow_picking_reservation'):
            return

        def apply_rule(clauses, params, tables, parent_model=None):
            """ :param parent_model: name of the parent model, if the added
                    clause comes from a parent model
            """
            if clauses:
                if parent_model:
                    # as inherited rules are being applied, we need to add the
                    # missing JOIN to reach the parent table (if not JOINed yet)
                    parent_table = '"%s"' % self.env[parent_model]._table
                    parent_alias = '"%s"' % self._inherits_join_add(self, parent_model, query)
                    # inherited rules are applied on the external table, replace
                    # parent_table by parent_alias
                    clauses = [clause.replace(parent_table, parent_alias) for clause in clauses]
                    # replace parent_table by parent_alias, and introduce
                    # parent_alias if needed
                    tables = [
                        (parent_table + ' as ' + parent_alias) if table == parent_table \
                            else table.replace(parent_table, parent_alias)
                        for table in tables
                    ]
                query.where_clause += clauses
                query.where_clause_params += params
                for table in tables:
                    if table not in query.tables:
                        query.tables.append(table)

        if self._transient:
            # One single implicit access rule for transient models: owner only!
            # This is ok because we assert that TransientModels always have
            # log_access enabled, so that 'create_uid' is always there.
            domain = [('create_uid', '=', self._uid)]
            tquery = self._where_calc(domain, active_test=False)
            apply_rule(tquery.where_clause, tquery.where_clause_params, tquery.tables)
            return

        # apply main rules on the object
        Rule = self.env['ir.rule']
        where_clause, where_params, tables = Rule.domain_get(self._name, mode)
        apply_rule(where_clause, where_params, tables)

        # apply ir.rules from the parents (through _inherits)
        for parent_model in self._inherits:
            where_clause, where_params, tables = Rule.domain_get(parent_model, mode)
            apply_rule(where_clause, where_params, tables, parent_model)
