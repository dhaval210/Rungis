# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from collections import OrderedDict

from psycopg2 import OperationalError

from odoo import api, models, registry
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, supplier):
        res = super(StockRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, values,
                                                                  po, supplier)
        if product_id._is_cw_product() and values.get('cw_qty'):
            product_cw_qty = values['cw_qty']
            product_cw_uom = self.env['uom.uom'].browse(values['cw_uom'])
            procurement_cw_uom_po_qty = product_cw_uom._compute_quantity(product_cw_qty, product_id.cw_uom_id)
            res['product_cw_uom_qty'] = procurement_cw_uom_po_qty
            res['product_cw_uom'] = product_cw_uom.id
        elif product_id._is_cw_product() and values.get('product_cw_uom_qty'):
            product_cw_qty = values['product_cw_uom_qty']
            res['product_cw_uom_qty'] = product_cw_qty
            res['product_cw_uom'] = product_id.cw_uom_id.id
        return res

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, values, line, partner):
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom, values,
                                                                 line, partner)
        if product_id._is_cw_product() and values.get('cw_qty'):
            product_cw_qty = values['cw_qty']
            product_cw_uom = self.env['uom.uom'].browse(values['cw_uom'])
            procurement_cw_uom_po_qty = product_cw_uom._compute_quantity(product_cw_qty, product_id.cw_uom_id)
            res['product_cw_uom_qty'] = line.product_cw_uom_qty + procurement_cw_uom_po_qty
            res['product_cw_uom'] = product_cw_uom.id
        elif product_id._is_cw_product() and values.get('product_cw_uom_qty'):
            product_cw_qty = values['product_cw_uom_qty']
            res['product_cw_uom_qty'] = line.product_cw_uom_qty + product_cw_qty
            res['product_cw_uom'] = product_id.cw_uom_id.id
        else:
            line.product_cw_uom_qty = 0
            line.product_cw_uom = None
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=False):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(ProcurementGroup, self)._procure_orderpoint_confirm(use_new_cursor, company_id)

        if company_id and self.env.user.company_id.id != company_id:
            self = self.with_context(company_id=company_id, force_company=company_id)
        OrderPoint = self.env['stock.warehouse.orderpoint']
        domain = self._get_orderpoint_domain(company_id=company_id)
        orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(domain,
                                                                                       order=self._procurement_from_orderpoint_get_order()).ids
        while orderpoints_noprefetch:
            if use_new_cursor:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))
            OrderPoint = self.env['stock.warehouse.orderpoint']

            orderpoints = OrderPoint.browse(orderpoints_noprefetch[:1000])
            orderpoints_noprefetch = orderpoints_noprefetch[1000:]

            location_data = OrderedDict()

            def makedefault():
                return {
                    'products': self.env['product.product'],
                    'orderpoints': self.env['stock.warehouse.orderpoint'],
                    'groups': []
                }

            for orderpoint in orderpoints:
                key = self._procurement_from_orderpoint_get_grouping_key([orderpoint.id])
                if not location_data.get(key):
                    location_data[key] = makedefault()
                location_data[key]['products'] += orderpoint.product_id
                location_data[key]['orderpoints'] += orderpoint
                location_data[key]['groups'] = self._procurement_from_orderpoint_get_groups([orderpoint.id])

            for location_id, location_data in location_data.items():
                location_orderpoints = location_data['orderpoints']
                product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
                substract_quantity = location_orderpoints._quantity_in_progress()
                substract_cw_quantity = location_orderpoints._cw_quantity_in_progress()

                for group in location_data['groups']:
                    if group.get('from_date'):
                        product_context['from_date'] = group['from_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    if group['to_date']:
                        product_context['to_date'] = group['to_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    product_quantity = location_data['products'].with_context(product_context)._product_available()
                    for orderpoint in location_orderpoints:
                        try:
                            op_product_virtual = product_quantity[orderpoint.product_id.id]['virtual_available']
                            op_product_cw_virtual = product_quantity[orderpoint.product_id.id]['cw_virtual_available']
                            qty = max(orderpoint.product_min_qty,
                                      orderpoint.product_max_qty) - op_product_virtual
                            cw_qty = max(orderpoint.product_min_cw_qty,
                                         orderpoint.product_max_cw_qty) - op_product_cw_virtual
                            remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0
                            cw_remainder = orderpoint.qty_multiple > 0 and cw_qty % orderpoint.qty_multiple or 0.0

                            if float_compare(remainder, 0.0,
                                             precision_rounding=orderpoint.product_uom.rounding) > 0:
                                qty += orderpoint.qty_multiple - remainder
                            if float_compare(cw_remainder, 0.0,
                                             precision_rounding=orderpoint.product_cw_uom.rounding) > 0:
                                cw_qty += orderpoint.qty_multiple - cw_remainder

                            compare_qty = qty
                            compare_cw_qty = cw_qty
                            qty -= substract_quantity[orderpoint.id]
                            cw_qty -= substract_cw_quantity[orderpoint.id]
                            qty_rounded = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)
                            cw_qty_rounded = float_round(cw_qty, precision_rounding=orderpoint.product_cw_uom.rounding)
                            if orderpoint.reordering_based_on == 'cwuom':
                                if op_product_cw_virtual is None:
                                    continue
                                if float_compare(op_product_cw_virtual, orderpoint.product_min_qty,
                                                 precision_rounding=orderpoint.product_uom.rounding) <= 0:

                                    if float_compare(compare_cw_qty, 0.0,
                                                     precision_rounding=orderpoint.product_cw_uom.rounding) < 0:
                                        continue
                                    if cw_qty_rounded > 0:
                                        qty_order = max(orderpoint.product_min_qty,
                                                        orderpoint.product_max_qty)
                                        qty_order = cw_qty_rounded / orderpoint.product_id.average_cw_quantity if orderpoint.product_id.average_cw_quantity > 0 else qty_order
                                        values = orderpoint._prepare_procurement_values(qty_order,
                                                                                        **group['procurement_values'])
                                        values.update({'product_cw_uom_qty': cw_qty_rounded,
                                                       'product_cw_uom': orderpoint.product_cw_uom.id})
                                        try:
                                            with self._cr.savepoint():
                                                self.env['procurement.group'].run(orderpoint.product_id, qty_order,
                                                                                  orderpoint.product_uom,
                                                                                  orderpoint.location_id,
                                                                                  orderpoint.name, orderpoint.name,
                                                                                  values)
                                        except UserError as error:
                                            self.env['stock.rule']._log_next_activity(orderpoint.product_id, error.name)
                                        self._procurement_from_orderpoint_post_process([orderpoint.id])
                                    if use_new_cursor:
                                        cr.commit()
                            else:
                                if op_product_virtual is None:
                                    continue
                                if float_compare(op_product_virtual, orderpoint.product_min_qty,
                                                 precision_rounding=orderpoint.product_uom.rounding) <= 0:

                                    if float_compare(compare_qty, 0.0,
                                                     precision_rounding=orderpoint.product_uom.rounding) < 0:
                                        continue
                                    if qty_rounded > 0:
                                        cw_qty_order = max(orderpoint.product_min_qty,
                                                           orderpoint.product_max_qty)
                                        cw_qty_order = qty_rounded * orderpoint.product_id.average_cw_quantity if orderpoint.product_id.average_cw_quantity > 0 else cw_qty_order

                                        values = orderpoint._prepare_procurement_values(qty_rounded,
                                                                                        **group['procurement_values'])
                                        values.update({'product_cw_uom_qty': cw_qty_order,
                                                       'product_cw_uom': orderpoint.product_cw_uom.id})

                                        try:
                                            with self._cr.savepoint():
                                                self.env['procurement.group'].run(orderpoint.product_id, qty_rounded,
                                                                                  orderpoint.product_uom,
                                                                                  orderpoint.location_id,
                                                                                  orderpoint.name, orderpoint.name,
                                                                                  values)
                                        except UserError as error:
                                            self.env['stock.rule']._log_next_activity(orderpoint.product_id, error.name)
                                        self._procurement_from_orderpoint_post_process([orderpoint.id])
                                    if use_new_cursor:
                                        cr.commit()

                        except OperationalError:
                            if use_new_cursor:
                                orderpoints_noprefetch += [orderpoint.id]
                                cr.rollback()
                                continue
                            else:
                                raise

            try:
                if use_new_cursor:
                    cr.commit()
            except OperationalError:
                if use_new_cursor:
                    cr.rollback()
                    continue
                else:
                    raise

            if use_new_cursor:
                cr.commit()
                cr.close()

        return {}

