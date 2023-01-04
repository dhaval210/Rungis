# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, _
from odoo.tools import float_round


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        lines = super(ReportBomStructure, self)._get_bom(bom_id, product_id, line_qty, line_id, level)
        bom = self.env['mrp.bom'].browse(bom_id)
        product = lines.get('product')
        bom_cw_quantity = (line_qty / lines.get('bom').product_qty) * lines.get('bom').cw_product_qty
        lines.update({
            'bom_cw_qty': bom_cw_quantity
        })
        if product._is_price_based_on_cw('purchase'):
            lines['price'] = product.cw_uom_id._compute_price(product.standard_price,
                                                              bom.product_cw_uom_id) * bom_cw_quantity
        return lines

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components, total = super(ReportBomStructure, self)._get_bom_lines(bom, bom_quantity, product, line_id, level)
        factor = bom_quantity / (bom.product_qty or 1.0)
        bom_cw_quantity = bom.cw_product_qty * factor
        n = 0
        total_cw = 0
        sub_total = 0
        for line in bom.bom_line_ids:
            if bom_cw_quantity:
                line_cw_quantity = (bom_cw_quantity / (bom.cw_product_qty or 1.0)) * line.cw_product_qty
            else:
                line_cw_quantity = factor * line.cw_product_qty

            price_cw = 0
            normal_price = 0.0
            if line.product_id._is_price_based_on_cw('purchase'):
                price_cw = line.product_id.cw_uom_id._compute_price(line.product_id.standard_price,
                                                                    line.product_cw_uom_id) * line_cw_quantity
                if line.child_bom_id:
                    factor = line.product_uom_id._compute_quantity(line.product_qty,
                                                                      line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                    sub_total = self._get_price(line.child_bom_id, factor, line.product_id)
                else:
                    sub_total = price_cw
                sub_total = self.env.user.company_id.currency_id.round(sub_total)
            for i in range(0, len(components)):
                components[n].update({
                    'prod_cw_qty': line_cw_quantity,
                    'prod_cw_uom': line.product_cw_uom_id.name
                })
                if line.product_id._is_price_based_on_cw('purchase'):
                    components[n]['prod_cost'] = self.env.user.company_id.currency_id.round(price_cw)
                    components[n]['total'] = self.env.user.company_id.currency_id.round(sub_total)
                else:
                    normal_price += components[n]['total']
                n += 1
                break
            if line.product_id._is_price_based_on_cw('purchase'):
                total_cw += sub_total
            else:
                total_cw += normal_price
        total = total_cw
        return components, total

    def _get_price(self, bom, factor, product):
        res = super(ReportBomStructure, self)._get_price(bom, factor, product)
        price = 0
        if bom.routing_id:
            operation_cycle = float_round(factor, precision_rounding=1, rounding_method='UP')
            operations = self._get_operation_line(bom.routing_id, operation_cycle, 0)
            price += sum([op['total'] for op in operations])
        for line in bom.bom_line_ids:
            if line._skip_bom_line(product):
                continue
            if line.child_bom_id:
                qty = line.product_uom_id._compute_quantity(line.product_qty * factor, line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_price = self._get_price(line.child_bom_id, qty, line.product_id)
                price += sub_price
            else:
                if line.product_id._is_price_based_on_cw('purchase'):
                    prod_cw_qty = line.cw_product_qty * factor
                    company = bom.company_id or self.env.company
                    not_rounded_price = line.product_id.uom_id._compute_price(line.product_id.with_context(force_comany=company.id).standard_price, line.product_uom_id) * prod_cw_qty
                    price += company.currency_id.round(not_rounded_price)
                else:
                    prod_qty = line.product_qty * factor
                    company = bom.company_id or self.env.company
                    not_rounded_price = line.product_id.uom_id._compute_price(
                        line.product_id.with_context(force_comany=company.id).standard_price,
                        line.product_uom_id) * prod_qty
                    price += company.currency_id.round(not_rounded_price)
        return price

    @api.model
    def _get_report_data(self, bom_id, searchQty=0, searchVariant=False):
        res = super(ReportBomStructure, self)._get_report_data(bom_id, searchQty, searchVariant)
        bom = self.env['mrp.bom'].browse(bom_id)
        bom_cw_quantity = searchQty or bom.cw_product_qty
        bom_cw_uom_name = ''
        if bom:
            bom_cw_uom_name = bom.product_cw_uom_id.name
        res.update({
            'bom_cw_uom_name': bom_cw_uom_name,
            'bom_cw_qty': bom_cw_quantity,
        })
        return res

    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(ReportBomStructure, self)._get_pdf_line(bom_id, product_id, qty, child_bom_ids,
                                                                 unfolded)

        data = self._get_bom(bom_id=bom_id, product_id=product_id.id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(bom_id=bom.id, product_id=product_id.id, line_qty=line_qty, line_id=line_id,
                                 level=level)
            bom_lines = data['components']
            lines = []
            for bom_line in bom_lines:
                lines.append({
                    'name': bom_line['prod_name'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'cw_quantity': bom_line['prod_cw_qty'],
                    'uom': bom_line['prod_uom'],
                    'cw_uom': bom_line['prod_cw_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code']
                })
                if bom_line['child_bom'] and (unfolded or bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (get_sub_lines(line.child_bom_id, line.product_id, bom_line['prod_qty'], line, level + 1))
            if data['operations']:
                lines.append({
                    'name': _('Operations'),
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    'uom': _('minutes'),
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    if unfolded or 'operation-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': operation['name'],
                            'type': 'operation',
                            'quantity': operation['duration_expected'],
                            'uom': _('minutes'),
                            'bom_cost': operation['total'],
                            'level': level + 1,
                        })
            return lines

        bom = self.env['mrp.bom'].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data['components'] = []
        data['lines'] = pdf_lines
        return data
