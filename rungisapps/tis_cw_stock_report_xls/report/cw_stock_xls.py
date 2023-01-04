# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import datetime
import pytz
from odoo import models, fields, api
from odoo.tools.float_utils import float_round
import operator as py_operator
from odoo.tools import pycompat

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class StockReportXls(models.AbstractModel):
    _name = 'report.tis_cw_stock_report_xls.cw_stock_report'
    _inherit = 'report.report_xlsx.abstract'

    @api.multi
    def _get_locations(self, warehouse):
        company_id = self.env.user.company_id.id
        if warehouse:
            res_domain = (
                [('location_id.company_id', '=', warehouse.id), ('location_id.usage', 'in', ['internal', 'transit'])],
                [('location_id.company_id', '=', False), ('location_dest_id.company_id', '=', warehouse.id)],
                [('location_id.company_id', '=', warehouse.id), ('location_dest_id.company_id', '=', False),
                 ])
        else:
            res_domain = (
                [('location_id.company_id', '=', company_id), ('location_id.usage', 'in', ['internal', 'transit'])],
                [('location_id.company_id', '=', False), ('location_dest_id.company_id', '=', company_id)],
                [('location_id.company_id', '=', company_id), ('location_dest_id.company_id', '=', False),
                 ])
        return res_domain

    @api.multi
    def get_line(self, obj, warehouse):
        category = obj.category_ids.mapped('id')
        products = self.env['product.product']
        if category:
            products = products.search([('type', '=', 'product'), ('categ_id', 'in', category)])
        else:
            products = products.search([('type', '=', 'product')])
        compute_at_date = obj.compute_at_date
        to_date = None
        if compute_at_date == 1:
            to_date = obj.date

        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_locations(warehouse)
        domain_quant = [('product_id', 'in', products.ids)] + domain_quant_loc
        cw_domain_quant_loc, cw_domain_move_in_loc, cw_domain_move_out_loc = self._get_locations(warehouse)
        cw_domain_quant = [('product_id', 'in', products.ids)] + cw_domain_quant_loc
        dates_in_the_past = False
        if to_date and to_date < fields.Datetime.now():  # Only to_date as to_date will correspond to qty_available
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', products.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', products.ids)] + domain_move_out_loc
        cw_domain_move_in = [('product_id', 'in', products.ids)] + cw_domain_move_in_loc
        cw_domain_move_out = [('product_id', 'in', products.ids)] + cw_domain_move_out_loc

        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
            cw_domain_move_in_done = list(cw_domain_move_in)
            cw_domain_move_out_done = list(cw_domain_move_out)

        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]
            cw_domain_move_in += [('date', '<=', to_date)]
            cw_domain_move_out += [('date', '<=', to_date)]

        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_in
        domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in
                            Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'],
                                            orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in
                             Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'],
                                             orderby='id'))
        quants_res = dict((item['product_id'][0], item['quantity']) for item in
                          Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        cw_domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + cw_domain_move_in
        cw_domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + cw_domain_move_out

        cw_moves_in_res = dict((item['product_id'][0], item['cw_product_qty']) for item in
                               Move.read_group(cw_domain_move_in_todo, ['product_id', 'cw_product_qty'], ['product_id'],
                                               orderby='id'))
        cw_moves_out_res = dict((item['product_id'][0], item['product_cw_uom_qty']) for item in
                                Move.read_group(cw_domain_move_out_todo, ['product_id', 'product_cw_uom_qty'],
                                                ['product_id'], orderby='id'))
        cw_quants_res = dict((item['product_id'][0], item['cw_stock_quantity']) for item in
                             Quant.read_group(cw_domain_quant, ['product_id', 'cw_stock_quantity'], ['product_id'],
                                              orderby='id'))
        if dates_in_the_past:
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                     Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'],
                                                     orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                      Move.read_group(domain_move_out_done, ['product_id', 'product_qty'],
                                                      ['product_id'], orderby='id'))
            cw_domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + cw_domain_move_in_done
            cw_domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + cw_domain_move_out_done
            cw_moves_in_res_past = dict((item['product_id'][0], item['cw_product_qty']) for item in
                                        Move.read_group(cw_domain_move_in_done, ['product_id', 'cw_product_qty'],
                                                        ['product_id'], orderby='id'))
            cw_moves_out_res_past = dict((item['product_id'][0], item['cw_product_qty']) for item in
                                         Move.read_group(cw_domain_move_out_done, ['product_id', 'cw_product_qty'],
                                                         ['product_id'], orderby='id'))

        val = dict()
        for product in products:
            product_id = product.id
            rounding = product.uom_id.rounding

            val[product_id] = {}
            if dates_in_the_past:
                qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id,
                                                                                        0.0) + moves_out_res_past.get(
                    product_id, 0.0)
                cw_qty_available = cw_quants_res.get(product_id, 0.0) - cw_moves_in_res_past.get(product_id,
                                                                                                 0.0) + cw_moves_out_res_past.get(
                    product_id, 0.0)
            else:
                qty_available = quants_res.get(product_id, 0.0)
                cw_qty_available = cw_quants_res.get(product_id, 0.0)

            val[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
            val[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0),
                                                          precision_rounding=rounding)
            val[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0),
                                                          precision_rounding=rounding)
            val[product_id]['virtual_available'] = float_round(
                qty_available + val[product_id]['incoming_qty'] - val[product_id]['outgoing_qty'],
                precision_rounding=rounding)
            val[product_id]['cw_qty_available'] = cw_qty_available
            val[product_id]['cw_incoming_qty'] = cw_moves_in_res.get(product_id, 0.0)
            val[product_id]['cw_outgoing_qty'] = cw_moves_out_res.get(product_id, 0.0)
            val[product_id]['cw_virtual_available'] = cw_qty_available + val[product_id]['cw_incoming_qty'] - \
                                                      val[product_id]['cw_outgoing_qty']
        lines = []
        StockMove = self.env['stock.move']
        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))
        for product in products:
            product_id = product.id
            if product.cost_method in ['standard', 'average']:
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                if product._is_price_based_on_cw('purchase'):
                    val[product_id]['stock_value'] = price_used * val[product_id]['cw_qty_available']
                else:
                    val[product_id]['stock_value'] = price_used * val[product_id]['qty_available']
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        domain = [('product_id', '=', product.id),
                                  ('date', '<=', to_date)] + StockMove._get_all_base_domain()
                        moves = StockMove.search(domain)
                        val[product_id]['stock_value'] = sum(moves.mapped('value'))

                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        val[product_id]['stock_value'] = value
                else:
                    val[product_id]['stock_value'], moves = product._sum_remaining_values()

            if val[product_id]['qty_available'] != 0:
                vals = {
                    'item_code': product.default_code,
                    'name': product.name,
                    'category': product.categ_id.name,
                    'cost_price': product.standard_price,
                    'available': val[product_id]['qty_available'],
                    'virtual_available': val[product_id]['virtual_available'],
                    'cw_available': val[product_id]['cw_qty_available'],
                    'cw_virtual_available': val[product_id]['cw_virtual_available'],
                    'total_value': val[product_id]['stock_value'],
                }
                lines.append(vals)

        return lines

    @api.multi
    def generate_xlsx_report(self, workbook, data, wizard_obj):
        stock_warehouses = []
        company_id = self.env.user.company_id
        for value in wizard_obj.warehouse_ids:
            stock_warehouses.append(value)
        if wizard_obj.warehouse_ids:
            for warehouse in stock_warehouses:
                get_line = self.get_line(wizard_obj, warehouse)
                sheet = workbook.add_worksheet(warehouse.name)
                format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
                format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
                format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
                format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
                format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
                format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
                font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
                font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
                font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
                red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
                justify = workbook.add_format({'font_size': 12})
                format3.set_align('center')
                justify.set_align('justify')
                format1.set_align('center')
                red_mark.set_align('center')
                sheet.merge_range(1, 7, 2, 10, 'CW Stock Report', format0)
                cat = ', '
                c = []
                category = wizard_obj.category_ids.mapped('id')
                if category:
                    for i in category:
                        c.append(self.env['product.category'].browse(i).name)
                    cat = cat.join(c)
                    sheet.merge_range(4, 0, 4, 1, 'Category(s) : ', format4)
                    sheet.merge_range(4, 2, 4, 3 + len(category), cat, format4)
                user = self.env['res.users'].browse(self.env.uid)
                tz = pytz.timezone(user.tz)
                time = pytz.utc.localize(datetime.now()).astimezone(tz)
                sheet.merge_range('A8:G8', 'Report Date: ' + str(time.strftime("%Y-%m-%d %H:%M %p")), format1)
                sheet.merge_range(7, 7, 7, 16, 'Warehouse', format1)
                sheet.merge_range('A9:G9', 'Product Information', format11)
                w_col_no = 6
                w_col_no1 = 7
                w_col_no = w_col_no + 10
                sheet.merge_range(8, w_col_no1, 8, w_col_no, warehouse.name, format11)
                sheet.write(9, 0, 'Item Code', format21)
                sheet.merge_range(9, 1, 9, 3, 'Name', format21)
                sheet.merge_range(9, 4, 9, 5, 'Category', format21)
                sheet.write(9, 6, 'Cost Price', format21)
                p_col_no1 = 7
                sheet.merge_range(9, p_col_no1, 9, p_col_no1 + 1, 'Available', format21)
                sheet.merge_range(9, p_col_no1 + 2, 9, p_col_no1 + 3, 'CW Available', format21)
                sheet.merge_range(9, p_col_no1 + 4, 9, p_col_no1 + 5, 'Forecasted Qty', format21)
                sheet.merge_range(9, p_col_no1 + 6, 9, p_col_no1 + 7, 'CW Forecasted Qty', format21)
                sheet.merge_range(9, p_col_no1 + 8, 9, p_col_no1 + 9, 'Valuation', format21)
                prod_row = 10
                prod_col = 0
                for each in get_line:
                    sheet.write(prod_row, prod_col, each['item_code'], font_size_8)
                    sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8_l)
                    sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8_l)
                    sheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8_r)
                    prod_row = prod_row + 1
                prod_row = 10
                prod_col = 7
                for each in get_line:
                    if each['available'] < 0:
                        sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, each['available'], red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, each['available'], font_size_8)
                    if each['cw_available'] < 0:
                        sheet.merge_range(prod_row, prod_col + 2, prod_row, prod_col + 3, each['cw_available'],
                                          red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col + 2, prod_row, prod_col + 3, each['cw_available'],
                                          font_size_8)
                    if each['virtual_available'] < 0:
                        sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['virtual_available'],
                                          red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['virtual_available'],
                                          font_size_8)
                    if each['cw_virtual_available'] < 0:
                        sheet.merge_range(prod_row, prod_col + 6, prod_row, prod_col + 7, each['cw_virtual_available'],
                                          red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col + 6, prod_row, prod_col + 7, each['cw_virtual_available'],
                                          font_size_8)
                    if each['total_value'] < 0:
                        sheet.merge_range(prod_row, prod_col + 8, prod_row, prod_col + 9, each['total_value'], red_mark)
                    else:
                        sheet.merge_range(prod_row, prod_col + 8, prod_row, prod_col + 9, each['total_value'],
                                          font_size_8_r)
                    prod_row = prod_row + 1
        else:
            get_line = self.get_line(wizard_obj, warehouse=None)
            sheet = workbook.add_worksheet('Stock Info')
            format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
            format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
            format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
            format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
            font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
            font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
            font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
            red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
            justify = workbook.add_format({'font_size': 12})
            format3.set_align('center')
            justify.set_align('justify')
            format1.set_align('center')
            red_mark.set_align('center')
            sheet.merge_range(1, 7, 2, 10, 'CW Stock Report', format0)
            cat = ', '
            c = []
            category = wizard_obj.category_ids.mapped('id')
            if category:
                for i in category:
                    c.append(self.env['product.category'].browse(i).name)
                cat = cat.join(c)
                sheet.merge_range(4, 0, 4, 1, 'Category(s) : ', format4)
                sheet.merge_range(4, 2, 4, 3 + len(category), cat, format4)
            user = self.env['res.users'].browse(self.env.uid)
            tz = pytz.timezone(user.tz)
            time = pytz.utc.localize(datetime.now()).astimezone(tz)
            sheet.merge_range('A8:G8', 'Report Date: ' + str(time.strftime("%Y-%m-%d %H:%M %p")), format1)
            sheet.merge_range(7, 7, 7, 16, 'Warehouse', format1)
            sheet.merge_range('A9:G9', 'Product Information', format11)
            w_col_no = 6
            w_col_no1 = 7
            w_col_no = w_col_no + 10
            sheet.merge_range(8, w_col_no1, 8, w_col_no, company_id.name, format11)
            sheet.write(9, 0, 'Item Code', format21)
            sheet.merge_range(9, 1, 9, 3, 'Name', format21)
            sheet.merge_range(9, 4, 9, 5, 'Category', format21)
            sheet.write(9, 6, 'Cost Price', format21)
            p_col_no1 = 7
            sheet.merge_range(9, p_col_no1, 9, p_col_no1 + 1, 'Available', format21)
            sheet.merge_range(9, p_col_no1 + 2, 9, p_col_no1 + 3, 'CW Available', format21)
            sheet.merge_range(9, p_col_no1 + 4, 9, p_col_no1 + 5, 'Forecasted Qty', format21)
            sheet.merge_range(9, p_col_no1 + 6, 9, p_col_no1 + 7, 'CW Forecasted Qty', format21)
            sheet.merge_range(9, p_col_no1 + 8, 9, p_col_no1 + 9, 'Value', format21)
            prod_row = 10
            prod_col = 0
            for each in get_line:
                sheet.write(prod_row, prod_col, each['item_code'], font_size_8)
                sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8_l)
                sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8_l)
                sheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8_r)
                prod_row = prod_row + 1
            prod_row = 10
            prod_col = 7
            for each in get_line:
                if each['available'] < 0:
                    sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, each['available'], red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col, prod_row, prod_col + 1, each['available'], font_size_8)
                if each['cw_available'] < 0:
                    sheet.merge_range(prod_row, prod_col + 2, prod_row, prod_col + 3, each['cw_available'],
                                      red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 2, prod_row, prod_col + 3, each['cw_available'],
                                      font_size_8)
                if each['virtual_available'] < 0:
                    sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['virtual_available'],
                                      red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['virtual_available'],
                                      font_size_8)
                if each['cw_virtual_available'] < 0:
                    sheet.merge_range(prod_row, prod_col + 6, prod_row, prod_col + 7, each['cw_virtual_available'],
                                      red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 6, prod_row, prod_col + 7, each['cw_virtual_available'],
                                      font_size_8)
                if each['total_value'] < 0:
                    sheet.merge_range(prod_row, prod_col + 8, prod_row, prod_col + 9, each['total_value'], red_mark)
                else:
                    sheet.merge_range(prod_row, prod_col + 8, prod_row, prod_col + 9, each['total_value'],
                                      font_size_8_r)
                prod_row = prod_row + 1
